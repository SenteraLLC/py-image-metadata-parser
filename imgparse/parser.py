"""MetadataParser class definition."""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from s3path import S3Path

from imgparse import xmp_tags
from imgparse.altitude import AltitudeSource, hit_terrain_api, parse_session_alt
from imgparse.exceptions import ParsingError, TerrainAPIError
from imgparse.getters import get_exif_data, get_xmp_data
from imgparse.pixel_pitches import PIXEL_PITCHES
from imgparse.rotations import apply_rotational_offset
from imgparse.types import Coords, Dimensions, Euler, PixelCoords, Version
from imgparse.util import convert_to_degrees, convert_to_float, parse_seq

logger = logging.getLogger(__name__)


class MetadataParser:
    """Metadata parsing class."""

    def __init__(self, image_path: Path | str | S3Path):
        """Initialize metadata parser."""
        if isinstance(image_path, str):
            if image_path[:4] == "s3://":
                image_path = S3Path.from_uri(image_path)
            else:
                image_path = Path(image_path)

        self.image_path = image_path

        # Lazily load exif and xmp data via properties
        self._exif_data: dict[str, Any] | None = None
        self._xmp_data: dict[str, Any] | None = None

    @property
    def exif_data(self) -> dict[str, Any]:
        """Get the exif data for the image."""
        if self._exif_data is None:
            self._exif_data = get_exif_data(self.image_path)
        return self._exif_data

    @property
    def xmp_data(self) -> dict[str, Any]:
        """Get the xmp data for the image."""
        if self._xmp_data is None:
            self._xmp_data = get_xmp_data(self.image_path)
        return self._xmp_data

    @property
    def xmp_tags(self) -> xmp_tags.XMPTags:
        """Get the xmp tag names associated with the image's sensor."""
        make, _ = self.get_make_and_model()
        if make == "Sentera":
            return xmp_tags.SenteraTags()
        elif make == "DJI" or make == "Hasselblad":
            return xmp_tags.DJITags()
        elif make == "MicaSense":
            return xmp_tags.MicaSenseTags()
        elif make == "Parrot":
            return xmp_tags.ParrotTags()
        else:
            return xmp_tags.XMPTags()

    def get_make_and_model(self) -> tuple[str, str]:
        """Get the make and model of the sensor that took the image."""
        try:
            return (
                self.exif_data["Image Make"].values,
                self.exif_data["Image Model"].values,
            )
        except KeyError:
            raise ParsingError(
                "Couldn't parse the make and model. Sensor might not be supported"
            )

    def get_firmware_version(self) -> Version:
        """
        Get the firmware version of the sensor.

        Expects camera firmware version to be in semver format (i.e. MAJOR.MINOR.PATCH), with an optional 'v'
        at the beginning.
        """
        try:
            version_match = re.search(
                "[0-9]+.[0-9]+.[0-9]+", self.exif_data["Image Software"].values
            )
            if not version_match:
                raise KeyError()
            major, minor, patch = version_match.group(0).split(".")
        except (KeyError, ValueError):
            raise ParsingError(
                "Couldn't parse sensor version. Sensor might not be supported"
            )

        return Version(int(major), int(minor), int(patch))

    def get_timestamp(self, format_string: str = "%Y:%m:%d %H:%M:%S") -> datetime:
        """
        Get the time stamp of an image and parse it into a `datetime` object with the given format string.

        If originating from a Sentera or DJI sensor, the format of the tag will likely be that of the default input.
        However, other sensors may store timestamps in other formats.

        :param format_string: Format code, as a string, to be used to parse the image timestamp.
        :return: **datetime_obj**: Parsed timestamp, in the format specified by the input format string.
        """
        try:
            import pytz
            from timezonefinder import TimezoneFinder
        except ImportError:
            logger.warning(
                "Module timezonefinder is required for retrieving timestamps."
                "Please execute `poetry install -E timestamps` to install this module."
            )
            raise

        try:
            datetime_obj = datetime.strptime(
                self.exif_data["EXIF DateTimeOriginal"].values, format_string
            )
        except KeyError:
            raise ParsingError(
                "Couldn't parse image timestamp. Sensor might not be supported"
            )
        except ValueError:
            raise ParsingError(
                "Couldn't parse found timestamp with given format string"
            )

        lat, lon = self.get_lat_lon()

        timezone = pytz.timezone(TimezoneFinder().timezone_at(lng=lon, lat=lat))
        make, _ = self.get_make_and_model()
        if make in ["Sentera", "MicaSense"]:
            datetime_obj = pytz.utc.localize(datetime_obj)
            # convert time to local timezone
            datetime_obj = datetime_obj.astimezone(timezone)
        else:
            datetime_obj = timezone.localize(datetime_obj)

        return datetime_obj

    def get_dimensions(self) -> Dimensions:
        """
        Get the height and width (in pixels) of the image.

        :return: **height**, **width** - the height and width of the image
        """
        make, model = self.get_make_and_model()
        ext = self.image_path.suffix.lower()

        try:
            if ext in [".jpg", ".jpeg"]:
                return Dimensions(
                    self.exif_data["EXIF ExifImageLength"].values[0],
                    self.exif_data["EXIF ExifImageWidth"].values[0],
                )
            elif ext in [".tif", ".tiff"]:
                return Dimensions(
                    self.exif_data["Image ImageLength"].values[0],
                    self.exif_data["Image ImageWidth"].values[0],
                )
            else:
                raise ParsingError(
                    f"Image format {ext} isn't supported for parsing height/width"
                )
        except KeyError:
            # Workaround for Sentera sensors missing the tags
            if make == "Sentera":
                if model.startswith("21030-"):
                    # 65R
                    return Dimensions(7000, 9344)
                elif model.startswith("21214-"):
                    # 6X RGB
                    return Dimensions(3888, 5184)
            raise ParsingError(
                "Couldn't parse the height and width of the image. Sensor might not be supported"
            )

    def get_pixel_pitch_meters(self) -> float:
        """
        Get pixel pitch (in meters) of the sensor that took the image.

        Non-Sentera cameras don't store the pixel pitch in the exif tags, so that is found in a lookup table.  See
        `pixel_pitches.py` to check which non-Sentera sensor models are supported and to add support for new sensors.

        :return: **pixel_pitch** - the pixel pitch of the camera in meters
        """
        make, model = self.get_make_and_model()
        try:
            if make == "Sentera":
                return (
                    1
                    / convert_to_float(self.exif_data["EXIF FocalPlaneXResolution"])
                    / 100
                )
            else:
                pixel_pitch = PIXEL_PITCHES[make][model]
        except KeyError:
            raise ParsingError(
                "Couldn't parse pixel pitch. Sensor might not be supported"
            )

        return pixel_pitch

    def get_focal_length_meters(self, use_calibrated: bool = False) -> float:
        """
        Get the focal length (in meters) of the sensor that took the image.

        :param use_calibrated: enable to use calibrated focal length if available
        :return: **focal_length** - the focal length of the camera in meters
        """
        if use_calibrated:
            try:
                return float(self.xmp_data[self.xmp_tags.FOCAL_LEN]) / 1000
            except KeyError:
                logger.warning(
                    "Calibrated focal length not found in XMP. Defaulting to uncalibrated focal length"
                )

        try:
            return convert_to_float(self.exif_data["EXIF FocalLength"]) / 1000
        except KeyError:
            raise ParsingError(
                "Couldn't parse the focal length. Sensor might not be supported"
            )

    def get_focal_length_pixels(
        self, use_calibrated_focal_length: bool = False
    ) -> float:
        """Get the focal length (in pixels) of the sensor that took the image."""
        fl = self.get_focal_length_meters(use_calibrated_focal_length)
        pp = self.get_pixel_pitch_meters()
        return fl / pp

    def get_principal_point(self) -> PixelCoords:
        """
        Get the principal point (x, y) in pixels of the sensor that took the image.

        :return: **principal_point** - a tuple of pixel coordinates of the principal point
        """
        try:
            pt = list(
                map(float, str(self.xmp_data[self.xmp_tags.PRINCIPAL_POINT]).split(","))
            )
            pp = self.get_pixel_pitch_meters()

            # convert point from mm from origin to px from origin
            ptx = pt[0] * 0.001 / pp
            pty = pt[1] * 0.001 / pp

            return PixelCoords(x=ptx, y=pty)
        except (KeyError, ValueError):
            raise ParsingError(
                "Couldn't find the principal point tag. Sensor might not be supported"
            )

    def get_distortion_parameters(self) -> list[float]:
        """Get the radial distortion parameters of the sensor that took the image."""
        try:
            return list(
                map(float, str(self.xmp_data[self.xmp_tags.DISTORTION]).split(","))
            )
        except (KeyError, ValueError):
            raise ParsingError(
                "Couldn't find the distortion tag. Sensor might not be supported"
            )

    def get_lat_lon(self) -> Coords:
        """
        Get the latitude and longitude of the sensor when the image was taken.

        :return: **latitude, longitude** - the location of where the image was taken
        """
        try:
            gps_latitude = self.exif_data["GPS GPSLatitude"]
            gps_latitude_ref = self.exif_data["GPS GPSLatitudeRef"]
            gps_longitude = self.exif_data["GPS GPSLongitude"]
            gps_longitude_ref = self.exif_data["GPS GPSLongitudeRef"]
        except KeyError:
            raise ParsingError("Couldn't parse lat/lon. Sensor might not be supported")

        lat = convert_to_degrees(gps_latitude)
        if gps_latitude_ref.values[0] != "N":
            lat = 0 - lat

        lon = convert_to_degrees(gps_longitude)
        if gps_longitude_ref.values[0] != "E":
            lon = 0 - lon

        return Coords(lat, lon)

    def get_roll_pitch_yaw(self, standardize: bool = True) -> Euler:
        """
        Get the orientation of the sensor (roll, pitch, yaw in degrees) when the image was taken.

        :param standardize: defaults to True. Standardizes roll, pitch, yaw to common reference frame (camera pointing down is pitch = 0)
        :return: **roll, pitch, yaw** - the orientation (degrees) of the camera with respect to the NED frame
        """
        try:
            rotation = Euler(
                float(self.xmp_data[self.xmp_tags.ROLL]),
                float(self.xmp_data[self.xmp_tags.PITCH]),
                float(self.xmp_data[self.xmp_tags.YAW]),
            )

            if standardize:
                make, _ = self.get_make_and_model()
                if make == "DJI" or make == "Hasselblad":
                    # DJI describes orientation in terms of the gimbal reference frame
                    # Thus camera pointing down is pitch = -90
                    # Apply pitch rotation of +90 to convert to standard reference frame
                    rotation = apply_rotational_offset(rotation, Euler(0, 90, 0))
        except KeyError:
            raise ParsingError(
                "Couldn't parse roll/pitch/yaw. Sensor might not be supported"
            )

        return rotation

    def get_altitude_msl(self) -> float:
        """
        Get the absolute altitude (meters above msl) of the sensor when the image was taken.

        :return: **altitude_msl** - the absolute altitude of the image in meters.
        """
        try:
            return convert_to_float(self.exif_data["GPS GPSAltitude"])
        except KeyError:
            raise ParsingError(
                "Couldn't parse altitude msl. Sensor might not be supported"
            )

    def get_relative_altitude(
        self,
        alt_source: AltitudeSource = AltitudeSource.default,
        terrain_api_key: str | None = None,
        fallback: bool = True,
    ) -> float:
        """
        Get the relative altitude of the sensor above the ground (in meters) when the image was taken.

        `alt_source` by default will grab the relative altitude stored in the image's xmp data. Other options are `lrf` to
        use the altitude detected from a laser range finder or `terrain` to use google's terrain api to correct the relative
        altitude with the terrain elevation change from the home point. If a non-default `alt_source` is specified and
        fails, the function will "fallback" and return the default xmp relative altitude instead. To disable this fallback
        and raise an error if the specified `alt_source` isn't available, set `fallback` to False.

        There is an additional fallback if the image is from an older firmware Sentera sensor. For older Sentera sensor's,
        this xmp tag will not exist, and instead the relative altitude must be computed using the `session.txt` file
        associated with the image instead.

        :param alt_source: Set to "lrf" for laser range finder. "terrain" for terrain aware altitude.
        :param terrain_api_key: Required if `alt_source` set to "terrain". API key to access google elevation api.
        :param fallback: If disabled and the specified `alt_source` fails, will throw an error instead of falling back.
        :return: **relative_alt** - the relative altitude of the camera above the ground
        """
        terrain_alt = 0.0

        try:
            if alt_source == AltitudeSource.lrf:
                return self._get_lrf_altitude()
            elif alt_source == AltitudeSource.terrain:
                terrain_alt = self._get_terrain_altitude(terrain_api_key)
        except (ParsingError, TerrainAPIError) as e:
            if not fallback:
                raise e
            logger.warning(f"{e}. Falling back to default relative altitude.")

        return self._get_relative_altitude_default() + terrain_alt

    def _get_relative_altitude_default(self) -> float:
        """Get default relative altitude."""
        make, _ = self.get_make_and_model()
        try:
            return float(self.xmp_data[self.xmp_tags.RELATIVE_ALT])
        except KeyError:
            if make == "Sentera":
                logger.warning(
                    "Relative altitude not found in XMP. Attempting to parse from session.txt file"
                )
                abs_alt = self.get_altitude_msl()
                session_alt = parse_session_alt(self.image_path)
                return abs_alt - session_alt
            else:
                raise ParsingError(
                    "Couldn't parse relative altitude from xmp data. Sensor may not be supported"
                )

    def _get_lrf_altitude(self) -> float:
        """Get altitude from laser range finder data stored in XMP."""
        try:
            try:
                return float(self.xmp_data[self.xmp_tags.LRF_ALT])
            except KeyError:
                # Specific logic to handle quad v1.0.0 incorrect tag
                return float(self.xmp_data[self.xmp_tags.LRF_ALT2])
        except KeyError:
            raise ParsingError("Altimeter LRF altitude not found in XMP data.")

    def _get_terrain_altitude(self, terrain_api_key: str | None = None) -> float:
        """Get terrain altitude relative to the home point."""
        home_lat, home_lon = self._get_home_point()
        image_lat, image_lon = self.get_lat_lon()
        home_elevation = hit_terrain_api(home_lat, home_lon, terrain_api_key)
        image_elevation = hit_terrain_api(image_lat, image_lon, terrain_api_key)
        return home_elevation - image_elevation

    def _get_home_point(self) -> tuple[float, float]:
        """
        Get the flight home point. Used for `get_relative_altitude(alt_source=terrain)`.

        :return: **lat**, **lon** - coordinates of flight home point
        """
        try:
            make, _ = self.get_make_and_model()
            if make == "DJI":
                self_data = self.xmp_data[self.xmp_tags.SELF_DATA].split("|")
                if len(self_data) == 4:
                    return float(self_data[0]), float(self_data[1])
                else:
                    raise KeyError()
            elif make == "Sentera":
                return float(self.xmp_data[self.xmp_tags.HOMEPOINT_LAT]), float(
                    self.xmp_data[self.xmp_tags.HOMEPOINT_LON]
                )
            else:
                raise KeyError()
        except KeyError:
            raise ParsingError(
                "Couldn't parse home point. Sensor might not be supported for terrain elevation parsing"
            )

    def get_gsd(
        self,
        use_calibrated_focal_length: bool = False,
        alt_source: AltitudeSource = AltitudeSource.default,
        terrain_api_key: str | None = None,
        fallback: bool = True,
    ) -> float:
        """
        Get the gsd of the image (in meters/pixel).

        :param use_calibrated_focal_length: enable to use calibrated focal length if available
        :param alt_source: See `get_relative_altitude()`
        :param terrain_api_key: See `get_relative_altitude()`
        :param fallback: See `get_relative_altitude()`
        :return: **gsd** - the ground sample distance of the image in meters
        """
        focal_length = self.get_focal_length_pixels(use_calibrated_focal_length)
        alt = self.get_relative_altitude(alt_source, terrain_api_key, fallback)

        if alt <= 0:
            raise ValueError("Parsed gsd is less than or equal to 0")

        return alt / focal_length

    def get_autoexposure(self) -> float:
        """
        Get the autoexposure value of the sensor when the image was taken.

        Autoexposure is derived from the integration time and gain of the sensor, which are stored in
        separate tags. This function retrieves those values and performs the calculation.

        :return: **autoexposure** - image autoexposure value
        """
        try:
            iso = float(self.exif_data["EXIF ISOSpeedRatings"].values[0])
            integration_time = convert_to_float(self.exif_data["EXIF ExposureTime"])
        except KeyError:
            raise ParsingError(
                "Couldn't parse either ISO or exposure time. Sensor might not be supported"
            )

        return iso * integration_time

    def get_ils(self) -> list[float]:
        """
        Get the ILS value of an image captured by a sensor with an ILS module.

        :param xmp_data: used internally for memoization. Not necessary to supply.
        :return: **ils** - ILS value of image, as a floating point number
        """
        try:
            return parse_seq(self.xmp_data[self.xmp_tags.ILS], float)
        except KeyError:
            raise ParsingError(
                "Couldn't parse ILS value. Sensor might not be supported"
            )

    def get_wavelength_data(self) -> tuple[list[int], list[int]]:
        """
        Get the central and FWHM wavelength values of an image.

        :return: **central_wavelength** - central wavelength of each band, as a list of ints
        :return: **wavelength_fwhm** - wavelength fwhm of each band, as a list of ints
        """
        try:
            try:
                central_wavelength = parse_seq(
                    self.xmp_data[self.xmp_tags.WAVELENGTH_CENTRAL], float
                )
                wavelength_fwhm = parse_seq(
                    self.xmp_data[self.xmp_tags.WAVELENGTH_FWHM], float
                )
            except TypeError:
                central_wavelength = [
                    float(self.xmp_data[self.xmp_tags.WAVELENGTH_CENTRAL])
                ]
                wavelength_fwhm = [float(self.xmp_data[self.xmp_tags.WAVELENGTH_FWHM])]

            return central_wavelength, wavelength_fwhm
        except KeyError:
            raise ParsingError(
                "Couldn't parse wavelength data. Sensor might not be supported"
            )

    def get_bandnames(self) -> list[str]:
        """
        Get the name of each band of an image.

        :return: **band_names** - name of each band of image, as a list of strings
        """
        try:
            try:
                return parse_seq(self.xmp_data[self.xmp_tags.BANDNAME])
            except TypeError:
                return [self.xmp_data[self.xmp_tags.BANDNAME]]
        except KeyError:
            raise ParsingError(
                "Couldn't parse bandnames. Sensor might not be supported"
            )

    def get_lens_model(self) -> str:
        """
        Get the lens model of an image from a Sentera Camera.

        :return: **lens_model** name of the lens model
        """
        try:
            make, _ = self.get_make_and_model()
            if make == "Sentera":
                # Exif LensModel is Single and D4K. Images LensModel is 6x
                return (
                    str(self.exif_data["Image LensModel"].values)
                    if self.exif_data.get("Image LensModel")
                    # will return KeyError if both are not found
                    else str(self.exif_data["EXIF LensModel"].values)
                )
            else:
                raise KeyError()

        except KeyError:
            raise ParsingError(
                "Couldn't parse lens model. Sensor might not be supported"
            )