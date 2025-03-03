"""MetadataParser class definition."""

import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from imgparse import xmp_tags
from imgparse.altitude import hit_terrain_api, parse_session_alt
from imgparse.exceptions import ParsingError, TerrainAPIError
from imgparse.pixel_pitches import PIXEL_PITCHES
from imgparse.rotations import apply_rotational_offset
from imgparse.s3 import S3Path
from imgparse.types import (
    AltitudeSource,
    Dimensions,
    Euler,
    PixelCoords,
    Version,
    WorldCoords,
)
from imgparse.util import (
    convert_to_degrees,
    convert_to_float,
    get_exif_data,
    get_xmp_data,
    parse_seq,
)

logger = logging.getLogger(__name__)


class MetadataParser:
    """Metadata parsing class."""

    def __init__(self, image_path: Path | str | S3Path, s3_role: str | None = None):
        """Initialize metadata parser."""
        if isinstance(image_path, str):
            if image_path[:5] == "s3://":
                image_path = S3Path.from_uri(image_path)
            else:
                image_path = Path(image_path)

        self.image_path = image_path
        self.s3_role = s3_role

        # Lazily load exif and xmp data
        self._exif_data: dict[str, Any] | None = None
        self._xmp_data: dict[str, Any] | None = None
        self._raw_data: bytes = b""

    @property
    def exif_data(self) -> dict[str, Any]:
        """Get the exif data for the image."""
        if self._exif_data is None:
            self._exif_data, self._raw_data = get_exif_data(
                self.image_path, self.s3_role, self._raw_data
            )
        return self._exif_data

    @property
    def xmp_data(self) -> dict[str, Any]:
        """Get the xmp data for the image."""
        if self._xmp_data is None:
            self._xmp_data, self._raw_data = get_xmp_data(
                self.image_path, self.s3_role, self._raw_data
            )
        return self._xmp_data

    @property
    def xmp_tags(self) -> xmp_tags.XMPTags:
        """Get the xmp tag names associated with the image's sensor."""
        if self.make() == "Sentera":
            return xmp_tags.SenteraTags()
        elif self.make() == "DJI" or self.make() == "Hasselblad":
            return xmp_tags.DJITags()
        elif self.make() == "MicaSense":
            return xmp_tags.MicaSenseTags()
        elif self.make() == "Parrot":
            return xmp_tags.ParrotTags()
        else:
            return xmp_tags.XMPTags()

    def make(self) -> str:
        """Get the make and model of the sensor that took the image."""
        try:
            return str(self.exif_data["Image Make"].values)
        except KeyError:
            raise ParsingError(
                "Couldn't parse the make and model. Sensor might not be supported"
            )

    def model(self) -> str:
        """Get the make and model of the sensor that took the image."""
        try:
            return str(self.exif_data["Image Model"].values)
        except KeyError:
            raise ParsingError(
                "Couldn't parse the make and model. Sensor might not be supported"
            )

    def firmware_version(self) -> Version:
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

    def timestamp(self, solar_time: bool = False) -> datetime:
        """
        Get the time stamp of an image and parse it into a `datetime` object.

        For Sentera sensors, the parsed datetime will be in utc. For DJI sensors, it will
        be the local time on the sensor. Set `solar_time=True` to convert Sentera timestamps
        to the approximate solar time based on the sensor's longitude.
        """
        try:
            timestamp = datetime.strptime(
                self.exif_data["EXIF DateTimeOriginal"].values, "%Y:%m:%d %H:%M:%S"
            )

            if solar_time and self.make() == "Sentera":
                _, lon = self.location()
                # longitude / 15 gives solar time offset
                offset_seconds = int((lon / 15.0) * 3600)
                timestamp += timedelta(seconds=offset_seconds)

            return timestamp
        except KeyError:
            raise ParsingError(
                "Couldn't parse image timestamp. Sensor might not be supported"
            )
        except ValueError:
            raise ParsingError(
                "Couldn't parse found timestamp with given format string"
            )

    def dimensions(self) -> Dimensions:
        """Get the height and width (in pixels) of the image."""
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
            if self.make() == "Sentera":
                if self.model().startswith("21030-"):
                    # 65R
                    return Dimensions(7000, 9344)
                elif self.model().startswith("21214-"):
                    # 6X RGB
                    return Dimensions(3888, 5184)
            raise ParsingError(
                "Couldn't parse the height and width of the image. Sensor might not be supported"
            )

    def pixel_pitch_meters(self) -> float:
        """
        Get pixel pitch (in meters) of the sensor that took the image.

        Non-Sentera cameras don't store the pixel pitch in the exif tags, so that is found in a lookup table.  See
        `pixel_pitches.py` to check which non-Sentera sensor models are supported and to add support for new sensors.
        """
        try:
            if self.make() == "Sentera":
                return (
                    1
                    / convert_to_float(self.exif_data["EXIF FocalPlaneXResolution"])
                    / 100
                )
            else:
                pixel_pitch = PIXEL_PITCHES[self.make()][self.model()]
        except KeyError:
            raise ParsingError(
                "Couldn't parse pixel pitch. Sensor might not be supported"
            )

        return pixel_pitch

    def focal_length_meters(self, use_calibrated: bool = False) -> float:
        """
        Get the focal length (in meters) of the sensor that took the image.

        :param use_calibrated: enable to use calibrated focal length if available
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

    def focal_length_pixels(self, use_calibrated_focal_length: bool = False) -> float:
        """Get the focal length (in pixels) of the sensor that took the image."""
        fl = self.focal_length_meters(use_calibrated_focal_length)
        pp = self.pixel_pitch_meters()
        return fl / pp

    def principal_point(self) -> PixelCoords:
        """Get the principal point (x, y) in pixels of the sensor that took the image."""
        try:
            pt = list(
                map(float, str(self.xmp_data[self.xmp_tags.PRINCIPAL_POINT]).split(","))
            )
            pp = self.pixel_pitch_meters()

            # convert point from mm from origin to px from origin
            ptx = pt[0] * 0.001 / pp
            pty = pt[1] * 0.001 / pp

            return PixelCoords(x=ptx, y=pty)
        except (KeyError, ValueError):
            raise ParsingError(
                "Couldn't find the principal point tag. Sensor might not be supported"
            )

    def distortion_parameters(self) -> list[float]:
        """Get the radial distortion parameters of the sensor that took the image."""
        try:
            return list(
                map(float, str(self.xmp_data[self.xmp_tags.DISTORTION]).split(","))
            )
        except (KeyError, ValueError):
            raise ParsingError(
                "Couldn't find the distortion tag. Sensor might not be supported"
            )

    def location(self) -> WorldCoords:
        """Get the latitude and longitude of the sensor when the image was taken."""
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

        return WorldCoords(lat, lon)

    def rotation(self, standardize: bool = True) -> Euler:
        """
        Get the orientation of the sensor (roll, pitch, yaw in degrees) when the image was taken.

        :param standardize: defaults to True. Standardizes roll, pitch, yaw to common reference frame (camera pointing down is pitch = 0)
        """
        try:
            rotation = Euler(
                float(self.xmp_data[self.xmp_tags.ROLL]),
                float(self.xmp_data[self.xmp_tags.PITCH]),
                float(self.xmp_data[self.xmp_tags.YAW]),
            )

            if standardize:
                if self.make() == "DJI" or self.make() == "Hasselblad":
                    # DJI describes orientation in terms of the gimbal reference frame
                    # Thus camera pointing down is pitch = -90
                    # Apply pitch rotation of +90 to convert to standard reference frame
                    rotation = apply_rotational_offset(rotation, Euler(0, 90, 0))
        except KeyError:
            raise ParsingError(
                "Couldn't parse roll/pitch/yaw. Sensor might not be supported"
            )

        return rotation

    def global_altitude(self) -> float:
        """Get the absolute altitude (meters above msl) of the sensor when the image was taken."""
        try:
            return convert_to_float(self.exif_data["GPS GPSAltitude"])
        except KeyError:
            raise ParsingError(
                "Couldn't parse altitude msl. Sensor might not be supported"
            )

    def relative_altitude(
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
        """
        terrain_alt = 0.0

        try:
            if alt_source == AltitudeSource.lrf:
                return self.lrf_altitude()
            elif alt_source == AltitudeSource.terrain:
                terrain_alt = self.terrain_altitude(terrain_api_key)
        except (ParsingError, TerrainAPIError) as e:
            if not fallback:
                raise e
            logger.warning(f"{e}. Falling back to default relative altitude.")

        return self.relative_altitude_default() + terrain_alt

    def relative_altitude_default(self) -> float:
        """Get default relative altitude."""
        try:
            return float(self.xmp_data[self.xmp_tags.RELATIVE_ALT])
        except KeyError:
            if self.make() == "Sentera":
                logger.warning(
                    "Relative altitude not found in XMP. Attempting to parse from session.txt file"
                )
                abs_alt = self.global_altitude()
                session_alt = parse_session_alt(self.image_path)
                return abs_alt - session_alt
            else:
                raise ParsingError(
                    "Couldn't parse relative altitude from xmp data. Sensor may not be supported"
                )

    def lrf_altitude(self) -> float:
        """Get altitude from laser range finder data stored in XMP."""
        try:
            try:
                return float(self.xmp_data[self.xmp_tags.LRF_ALT])
            except KeyError:
                # Specific logic to handle quad v1.0.0 incorrect tag
                return float(self.xmp_data[self.xmp_tags.LRF_ALT2])
        except KeyError:
            raise ParsingError("Altimeter LRF altitude not found in XMP data.")

    def terrain_altitude(self, terrain_api_key: str | None = None) -> float:
        """Get terrain altitude relative to the home point."""
        home_lat, home_lon = self.home_point()
        image_lat, image_lon = self.location()
        home_elevation = hit_terrain_api(home_lat, home_lon, terrain_api_key)
        image_elevation = hit_terrain_api(image_lat, image_lon, terrain_api_key)
        return home_elevation - image_elevation

    def home_point(self) -> WorldCoords:
        """Get the flight home point. Used for `get_relative_altitude(alt_source=terrain)`."""
        try:
            if self.make() == "DJI":
                self_data = self.xmp_data[self.xmp_tags.SELF_DATA].split("|")
                if len(self_data) == 4:
                    return WorldCoords(float(self_data[0]), float(self_data[1]))
                else:
                    raise KeyError()
            elif self.make() == "Sentera":
                return WorldCoords(
                    float(self.xmp_data[self.xmp_tags.HOMEPOINT_LAT]),
                    float(self.xmp_data[self.xmp_tags.HOMEPOINT_LON]),
                )
            else:
                raise KeyError()
        except KeyError:
            raise ParsingError(
                "Couldn't parse home point. Sensor might not be supported for terrain elevation parsing"
            )

    def gsd(
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
        """
        focal_length = self.focal_length_pixels(use_calibrated_focal_length)
        alt = self.relative_altitude(alt_source, terrain_api_key, fallback)

        if alt <= 0:
            raise ValueError("Parsed gsd is less than or equal to 0")

        return alt / focal_length

    def autoexposure(self) -> float:
        """
        Get the autoexposure value of the sensor when the image was taken.

        Autoexposure is derived from the integration time and gain of the sensor, which are stored in
        separate tags. This function retrieves those values and performs the calculation.
        """
        try:
            iso = float(self.exif_data["EXIF ISOSpeedRatings"].values[0])
            integration_time = convert_to_float(self.exif_data["EXIF ExposureTime"])
        except KeyError:
            raise ParsingError(
                "Couldn't parse either ISO or exposure time. Sensor might not be supported"
            )

        return iso * integration_time

    def ils(self) -> list[float]:
        """Get the ILS value of an image captured by a sensor with an ILS module."""
        try:
            if self.make() == "DJI":
                return [float(self.xmp_data[self.xmp_tags.ILS])]
            else:
                return parse_seq(self.xmp_data[self.xmp_tags.ILS], float)
        except KeyError:
            raise ParsingError(
                "Couldn't parse ILS value. Sensor might not be supported"
            )

    def wavelength_data(self) -> tuple[list[int], list[int]]:
        """Get the central and FWHM wavelength values of an image."""
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

    def bandnames(self) -> list[str]:
        """Get the name of each band of an image."""
        try:
            try:
                return parse_seq(self.xmp_data[self.xmp_tags.BANDNAME])
            except TypeError:
                return [self.xmp_data[self.xmp_tags.BANDNAME]]
        except KeyError:
            raise ParsingError(
                "Couldn't parse bandnames. Sensor might not be supported"
            )

    def lens_model(self) -> str:
        """Get the lens model of an image from a Sentera Camera."""
        try:
            return (
                str(self.exif_data["Image LensModel"].values)
                if self.exif_data.get("Image LensModel")
                # will return KeyError if both are not found
                else str(self.exif_data["EXIF LensModel"].values)
            )

        except KeyError:
            raise ParsingError(
                "Couldn't parse lens model. Sensor might not be supported"
            )

    def serial_number(self) -> int:
        """
        Get the serial number of the sensor.

        Expects serial number to be parsable as an integer.
        """
        try:
            return int(self.exif_data["Image BodySerialNumber"].values)
        except (KeyError, ValueError):
            raise ParsingError(
                "Couldn't parse sensor version. Sensor might not be supported"
            )

    def irradiance(self) -> float:
        """Get the Irradiance value of an image captured by a sensor with an DLS module."""
        try:
            return float(self.xmp_data[self.xmp_tags.IRRADIANCE])
        except KeyError:
            raise ParsingError(
                "Couldn't parse irradiance value. Sensor might not be supported"
            )

    def capture_id(self) -> str:
        """
        Get unique id for a single capture event.

        This unique id is consistent across bands for multispectral cameras.
        """
        try:
            if self.make() == "Sentera":
                try:
                    # Firmware version >=2.1.0
                    return f"{self.xmp_data['Camera:FlightUUID']}_{self.xmp_data['Camera:CaptureUUID']}"
                except KeyError:
                    # Firmware version <2.1.0
                    return f"{self.xmp_data['Camera:FlightUniqueID']}_{self.xmp_data['Camera:ImageUniqueID']}"
            else:
                return str(self.xmp_data[self.xmp_tags.CAPTURE_UUID])
        except KeyError:
            raise ParsingError("Couldn't determine unique id")

    def dewarp_flag(self) -> bool:
        """Get the dewarp flag of the image."""
        try:
            return bool(int(self.xmp_data[self.xmp_tags.DEWARP_FLAG]))
        except KeyError:
            raise ParsingError(
                "Couldn't parse dewarp flag. Sensor might not be supported"
            )
