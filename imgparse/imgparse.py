"""Extract metadata from exif and xmp tags in images."""

import logging
import os
import re
from datetime import datetime

import pytz
import requests

from imgparse import xmp
from imgparse.decorators import get_if_needed, memoize
from imgparse.exceptions import ParsingError, TerrainAPIError
from imgparse.getters import get_exif_data, get_xmp_data
from imgparse.pixel_pitches import PIXEL_PITCHES
from imgparse.rotations import apply_rotational_offset
from imgparse.types import Coords, Dimensions, Euler, PixelCoords, Version
from imgparse.util import convert_to_degrees, convert_to_float, parse_seq

logger = logging.getLogger(__name__)

TERRAIN_URL = "https://maps.googleapis.com/maps/api/elevation/json"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


@get_if_needed("exif_data", getter=get_exif_data, getter_args=["image_path"])
def get_make_and_model(image_path, exif_data=None):
    """
    Get the make and model of the sensor that took the image.

    :param image_path: the full path to the image
    :param exif_data: used internally for memoization. Not necessary to supply.
    :return: **make**, **model** - the make and model of the camera
    :raises: ParsingError
    """
    try:
        return exif_data["Image Make"].values, exif_data["Image Model"].values
    except KeyError:
        raise ParsingError(
            "Couldn't parse the make and model. Sensor might not be supported"
        )


@get_if_needed("exif_data", getter=get_exif_data, getter_args=["image_path"])
def get_firmware_version(image_path, exif_data=None):
    """
    Get the firmware version of the sensor.

    Expects camera firmware version to be in semver format (i.e. MAJOR.MINOR.PATCH), with an optional 'v'
    at the beginning.

    :param image_path: the full path to the image
    :param exif_data: used internally for memoization. Not necessary to supply.
    :return: **major**, **minor**, **patch** - sensor software version
    :raises: ParsingError
    """
    try:
        version_match = re.search(
            "[0-9]+.[0-9]+.[0-9]+", exif_data["Image Software"].values
        )
        if not version_match:
            raise KeyError()
        major, minor, patch = version_match.group(0).split(".")
    except KeyError or ValueError:
        raise ParsingError(
            "Couldn't parse sensor version. Sensor might not be supported"
        )

    return Version(int(major), int(minor), int(patch))


@get_if_needed("exif_data", getter=get_exif_data, getter_args=["image_path"])
def get_serial_number(image_path, exif_data=None):
    """
    Get the firmware version of the sensor.

    Expects camera firmware version to be in semver format (i.e. MAJOR.MINOR.PATCH), with an optional 'v'
    at the beginning.

    :param image_path: the full path to the image
    :param exif_data: used internally for memoization. Not necessary to supply.
    :return: **major**, **minor**, **patch** - sensor software version
    :raises: ParsingError
    """
    try:
        serial_no = int(exif_data["Image BodySerialNumber"].values)
    except (KeyError, ValueError):
        raise ParsingError(
            "Couldn't parse sensor version. Sensor might not be supported"
        )

    return serial_no


@get_if_needed("exif_data", getter=get_exif_data, getter_args=["image_path"])
def get_timestamp(image_path, exif_data=None, format_string="%Y:%m:%d %H:%M:%S"):
    """
    Get the time stamp of an image and parse it into a `datetime` object with the given format string.

    If originating from a Sentera or DJI sensor, the format of the tag will likely be that of the default input.
    However, other sensors may store timestamps in other formats.

    :param image_path: the full path to the image
    :param exif_data: used internally for memoization. Not necessary to supply.
    :param format_string: Format code, as a string, to be used to parse the image timestamp.
    :return: **datetime_obj**: Parsed timestamp, in the format specified by the input format string.
    :raises: ParsingError
    """
    try:
        from timezonefinder import TimezoneFinder
    except ImportError:
        logger.warning(
            "Module timezonefinder is required for retrieving timestamps."
            "Please execute `poetry install -E timestamps` to install this module."
        )
        raise

    try:
        datetime_obj = datetime.strptime(
            exif_data["EXIF DateTimeOriginal"].values, format_string
        )
    except KeyError:
        raise ParsingError(
            "Couldn't parse image timestamp. Sensor might not be supported"
        )
    except ValueError:
        raise ParsingError("Couldn't parse found timestamp with given format string")

    lat, lon = get_lat_lon(image_path, exif_data)

    timezone = pytz.timezone(TimezoneFinder().timezone_at(lng=lon, lat=lat))
    make, _ = get_make_and_model(image_path, exif_data)
    if make in ["Sentera", "MicaSense"]:
        datetime_obj = pytz.utc.localize(datetime_obj)
        # convert time to local timezone
        datetime_obj = datetime_obj.astimezone(timezone)
    else:
        datetime_obj = timezone.localize(datetime_obj)

    return datetime_obj


## Intrinsics


@get_if_needed("exif_data", getter=get_exif_data, getter_args=["image_path"])
def get_dimensions(image_path, exif_data=None):
    """
    Get the height and width (in pixels) of the image.

    :param image_path: the full path to the image
    :param exif_data: used internally for memoization. Not necessary to supply.
    :return: **height**, **width** - the height and width of the image
    :raises: ParsingError
    """
    make, model = get_make_and_model(image_path, exif_data)
    ext = os.path.splitext(image_path)[-1].lower()

    try:
        if ext in [".jpg", ".jpeg"]:
            return Dimensions(
                exif_data["EXIF ExifImageLength"].values[0],
                exif_data["EXIF ExifImageWidth"].values[0],
            )
        elif ext in [".tif", ".tiff"]:
            return Dimensions(
                exif_data["Image ImageLength"].values[0],
                exif_data["Image ImageWidth"].values[0],
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


@get_if_needed("exif_data", getter=get_exif_data, getter_args=["image_path"])
def get_pixel_pitch(image_path, exif_data=None):
    """
    Get pixel pitch (in meters) of the sensor that took the image.

    Non-Sentera cameras don't store the pixel pitch in the exif tags, so that is found in a lookup table.  See
    `pixel_pitches.py` to check which non-Sentera sensor models are supported and to add support for new sensors.

    :param image_path: the full path to the image
    :param exif_data: used internally for memoization. Not necessary to supply.
    :return: **pixel_pitch** - the pixel pitch of the camera in meters
    :raises: ParsingError
    """
    make, model = get_make_and_model(image_path, exif_data)
    try:
        if make == "Sentera":
            return 1 / convert_to_float(exif_data["EXIF FocalPlaneXResolution"]) / 100
        else:
            pixel_pitch = PIXEL_PITCHES[make][model]
    except KeyError:
        raise ParsingError("Couldn't parse pixel pitch. Sensor might not be supported")

    return pixel_pitch


@get_if_needed("exif_data", getter=get_exif_data, getter_args=["image_path"])
@get_if_needed("xmp_data", getter=get_xmp_data, getter_args=["image_path"])
def get_focal_length(image_path, exif_data=None, xmp_data=None, use_calibrated=False):
    """
    Get the focal length (in meters) of the sensor that took the image.

    :param image_path: the full path to the image
    :param exif_data: used internally for memoization. Not necessary to supply.
    :param xmp_data: used internally for memoization. Not necessary to supply.
    :param use_calibrated: enable to use calibrated focal length if available
    :return: **focal_length** - the focal length of the camera in meters
    :raises: ParsingError
    """
    if use_calibrated:
        try:
            make, _ = get_make_and_model(image_path, exif_data)
            xmp_tags = xmp.get_tags(make)
            return float(xmp_data[xmp_tags.FOCAL_LEN]) / 1000
        except KeyError:
            logger.warning(
                "Calibrated focal length not found in XMP. Defaulting to uncalibrated focal length"
            )

    try:
        return convert_to_float(exif_data["EXIF FocalLength"]) / 1000
    except KeyError:
        raise ParsingError(
            "Couldn't parse the focal length. Sensor might not be supported"
        )


@get_if_needed("exif_data", getter=get_exif_data, getter_args=["image_path"])
@get_if_needed("xmp_data", getter=get_xmp_data, getter_args=["image_path"])
def get_principal_point(
    image_path,
    exif_data=None,
    xmp_data=None,
):
    """
    Get the principal point (x, y) in pixels of the sensor that took the image.

    :param image_path: the full path to the image
    :param exif_data: used internally for memoization. Not necessary to supply.
    :param xmp_data: used internally for memoization. Not necessary to supply.
    :return: **principal_point** - a tuple of pixel coordinates of the principal point
    :raises: ParsingError
    """
    try:
        make, _ = get_make_and_model(image_path, exif_data)
        xmp_tags = xmp.get_tags(make)
        pt = list(map(float, str(xmp_data[xmp_tags.PRINCIPAL_POINT]).split(",")))
        pixel_pitch = get_pixel_pitch(image_path, exif_data)

        # convert point from mm from origin to px from origin
        ptx = pt[0] * 0.001 / pixel_pitch
        pty = pt[1] * 0.001 / pixel_pitch

        return PixelCoords(x=ptx, y=pty)
    except (KeyError, ValueError):
        raise ParsingError(
            "Couldn't find the principal point tag. Sensor might not be supported"
        )


@get_if_needed("exif_data", getter=get_exif_data, getter_args=["image_path"])
@get_if_needed("xmp_data", getter=get_xmp_data, getter_args=["image_path"])
def get_distortion_parameters(
    image_path,
    exif_data=None,
    xmp_data=None,
):
    """
    Get the radial distortion parameters of the sensor that took the image.

    :param image_path: the full path to the image
    :param exif_data: used internally for memoization. Not necessary to supply.
    :param xmp_data: used internally for memoization. Not necessary to supply.
    :return: **distortions** - a sequence of distortion parameters
    :raises: ParsingError
    """
    try:
        make, _ = get_make_and_model(image_path, exif_data)
        xmp_tags = xmp.get_tags(make)
        return list(map(float, str(xmp_data[xmp_tags.DISTORTION]).split(",")))
    except (KeyError, ValueError):
        raise ParsingError(
            "Couldn't find the distortion tag. Sensor might not be supported"
        )


@get_if_needed("exif_data", getter=get_exif_data, getter_args=["image_path"])
@get_if_needed("xmp_data", getter=get_xmp_data, getter_args=["image_path"])
def get_camera_params(
    image_path, exif_data=None, xmp_data=None, use_calibrated_focal_length=False
):
    """
    Get the focal length and pixel pitch (in meters) of the sensor that took the image.

    :param image_path: the full path to the image
    :param exif_data: used internally for memoization. Not necessary to supply.
    :param xmp_data: used internally for memoization. Not necessary to supply.
    :param use_calibrated_focal_length: enable to use calibrated focal length if available
    :return: **focal_length, pixel_pitch** - the camera parameters in meters
    :raises: ParsingError
    """
    focal_length = get_focal_length(
        image_path, exif_data, xmp_data, use_calibrated_focal_length
    )
    pixel_pitch = get_pixel_pitch(image_path, exif_data)

    return focal_length, pixel_pitch


@get_if_needed("exif_data", getter=get_exif_data, getter_args=["image_path"])
@get_if_needed("xmp_data", getter=get_xmp_data, getter_args=["image_path"])
def get_focal_length_pixels(
    image_path, exif_data=None, xmp_data=None, use_calibrated_focal_length=False
):
    """
    Get the focal length (in pixels) of the sensor that took the image.

    :param image_path: the full path to the image
    :param exif_data: used internally for memoization. Not necessary to supply.
    :param xmp_data: used internally for memoization. Not necessary to supply.
    :param use_calibrated_focal_length: enable to use calibrated focal length if available
    :return: **focal_length, pixel_pitch** - the camera parameters in meters
    :raises: ParsingError
    """
    focal_length, pixel_pitch = get_camera_params(
        image_path, exif_data, xmp_data, use_calibrated_focal_length
    )

    return focal_length / pixel_pitch


## Extrinsics


@get_if_needed("exif_data", getter=get_exif_data, getter_args=["image_path"])
def get_lat_lon(image_path, exif_data=None):
    """
    Get the latitude and longitude of the sensor when the image was taken.

    :param image_path: the full path to the image
    :param exif_data: used internally for memoization. Not necessary to supply.
    :return: **latitude, longitude** - the location of where the image was taken
    :raises: ParsingError
    """
    try:
        gps_latitude = exif_data["GPS GPSLatitude"]
        gps_latitude_ref = exif_data["GPS GPSLatitudeRef"]
        gps_longitude = exif_data["GPS GPSLongitude"]
        gps_longitude_ref = exif_data["GPS GPSLongitudeRef"]
    except KeyError:
        raise ParsingError("Couldn't parse lat/lon. Sensor might not be supported")

    lat = convert_to_degrees(gps_latitude)
    if gps_latitude_ref.values[0] != "N":
        lat = 0 - lat

    lon = convert_to_degrees(gps_longitude)
    if gps_longitude_ref.values[0] != "E":
        lon = 0 - lon

    return Coords(lat, lon)


@get_if_needed("exif_data", getter=get_exif_data, getter_args=["image_path"])
@get_if_needed("xmp_data", getter=get_xmp_data, getter_args=["image_path"])
def get_roll_pitch_yaw(image_path, exif_data=None, xmp_data=None, standardize=True):
    """
    Get the orientation of the sensor (roll, pitch, yaw in degrees) when the image was taken.

    :param image_path: the full path to the image
    :param exif_data: used internally for memoization. Not necessary to supply.
    :param xmp_data: used internally for memoization. Not necessary to supply.
    :param standardize: defaults to True. Standardizes roll, pitch, yaw to common reference frame (camera pointing down is pitch = 0)
    :return: **roll, pitch, yaw** - the orientation (degrees) of the camera with respect to the NED frame
    :raises: ParsingError
    """
    make, model = get_make_and_model(image_path, exif_data)
    xmp_tags = xmp.get_tags(make)

    try:
        rotation = Euler(
            float(xmp_data[xmp_tags.ROLL]),
            float(xmp_data[xmp_tags.PITCH]),
            float(xmp_data[xmp_tags.YAW]),
        )

        if standardize:
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


## Altitude


def parse_session_alt(image_path):
    """
    Get the session ground altitude (meters above msl) from a `session.txt` file.

    Used for Sentera cameras since relative altitude isn't stored in exif or xmp tags, and instead the session ground
    altitude is written as a text file that needs to be read.  The `session.txt` must be in the same directory as the
    image in order to be read.

    :param image_path: the full path to the image
    :return: **ground_alt** - the session ground altitude, used to calculate relative altitude.
    :raises: ParsingError
    """
    imagery_dir = os.path.dirname(image_path)
    session_path = os.path.join(imagery_dir, "session.txt")
    if not os.path.isfile(session_path):
        raise ParsingError("Couldn't find session.txt file in image directory")

    session_file = open(session_path, "r")
    session_alt = session_file.readline().split("\n")[0].split("=")[1]
    session_file.close()
    if not session_alt:
        raise ParsingError("Couldn't parse session altitude from session.txt")

    return float(session_alt)


@get_if_needed("exif_data", getter=get_exif_data, getter_args=["image_path"])
@get_if_needed("xmp_data", getter=get_xmp_data, getter_args=["image_path"])
def get_home_point(image_path, exif_data=None, xmp_data=None):
    """
    Get the flight home point. Used for `get_relative_altitude(alt_source=terrain)`.

    :param image_path: the full path to the image
    :param exif_data: used internally for memoization. Not necessary to supply.
    :param xmp_data: used internally for memoization. Not necessary to supply.
    :return: **lat**, **lon** - coordinates of flight home point
    """
    try:
        make, model = get_make_and_model(image_path, exif_data)
        xmp_tags = xmp.get_tags(make)
        if make == "DJI":
            self_data = xmp_data[xmp_tags.SELF_DATA].split("|")
            if len(self_data) == 4:
                return float(self_data[0]), float(self_data[1])
            else:
                raise KeyError()
        elif make == "Sentera":
            return float(xmp_data[xmp_tags.HOMEPOINT_LAT]), float(
                xmp_data[xmp_tags.HOMEPOINT_LON]
            )
        else:
            raise KeyError()
    except KeyError:
        logger.warning(
            "Couldn't parse home point. Sensor might not be supported for terrain elevation parsing"
        )
        raise ParsingError(
            "Couldn't parse home point. Sensor might not be supported for terrain elevation parsing"
        )


def _compute_terrain_offset(image_path, exif_data, xmp_data, api_key):
    """
    Get relative terrain elevation for the image from google's terrain api.

    Relative terrain elevation is the flight home point terrain elevation - the image terrain elevation.
    The relative altitude stored in an image's xmp data is relative to the home point takeoff, not the
    altitude of the drone above the ground at each image location. We add the relative terrain elevation
    to the relative altitude to get the actual altitude of the drone above the ground.
    """
    if api_key is None:
        api_key = GOOGLE_API_KEY

    home_lat, home_lon = get_home_point(image_path, exif_data, xmp_data)
    image_lat, image_lon = get_lat_lon(image_path, exif_data)
    home_elevation = _get_home_point_elevation(home_lat, home_lon, api_key)
    image_elevation = _get_terrain_elevation(image_lat, image_lon, api_key)
    return home_elevation - image_elevation


def _get_terrain_elevation(lat, lon, api_key):
    """Call out to the google elevation api to get the terrain elevation at a given lat/lon."""
    params = {
        "locations": f"{lat} {lon}",
        "key": api_key,
    }
    response = requests.request("GET", TERRAIN_URL, params=params).json()
    if response["status"] != "OK":
        logger.warning("Couldn't access google terrain api")
        raise TerrainAPIError("Couldn't access google terrain api")
    return response["results"][0]["elevation"]


@memoize
def _get_home_point_elevation(lat, lon, api_key):
    """
    Memoized wrapper around `get_terrain_elevation()`.

    Ensure we aren't making multiple calls to google to get the same home point elevation for images from the
    same flight.
    """
    return _get_terrain_elevation(lat, lon, api_key)


@get_if_needed("exif_data", getter=get_exif_data, getter_args=["image_path"])
@get_if_needed("xmp_data", getter=get_xmp_data, getter_args=["image_path"])
def get_relative_altitude(
    image_path,
    exif_data=None,
    xmp_data=None,
    alt_source="default",
    terrain_api_key=None,
    fallback=True,
):
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

    :param image_path: the full path to the image
    :param exif_data: used internally for memoization. Not necessary to supply.
    :param xmp_data: used internally for memoization. Not necessary to supply.
    :param alt_source: Set to "lrf" for laser range finder. "terrain" for terrain aware altitude.
    :param terrain_api_key: Required if `alt_source` set to "terrain". API key to access google elevation api.
    :param fallback: If disabled and the specified `alt_source` fails, will throw an error instead of falling back.
    :return: **relative_alt** - the relative altitude of the camera above the ground
    :raises: ParsingError
    """
    make, model = get_make_and_model(image_path, exif_data)
    xmp_tags = xmp.get_tags(make)
    terrain_alt = 0
    if alt_source == "lrf":
        try:
            try:
                return float(xmp_data[xmp_tags.LRF_ALT])
            except KeyError:
                # Specific logic to handle quad v1.0.0 incorrect tag
                return float(xmp_data[xmp_tags.LRF_ALT2])
        except KeyError:
            logger.warning(
                "Altimeter calculated altitude not found in XMP. Defaulting to relative altitude"
            )
    elif alt_source == "terrain":
        try:
            terrain_alt = _compute_terrain_offset(
                image_path, exif_data, xmp_data, terrain_api_key
            )
            # We set alt source to default here if successfully parsed terrain altitude
            # to avoid incorrectly failing below if fallback is set to False
            alt_source = "default"
        except ParsingError:
            logger.warning(
                "Couldn't determine terrain elevation. Defaulting to relative altitude"
            )
        except TerrainAPIError:
            if not fallback:
                raise

    if alt_source != "default" and not fallback:
        raise ParsingError(
            f"Fallback disabled. Couldn't parse relative altitude for given alt_source: {alt_source}"
        )

    try:
        return float(xmp_data[xmp_tags.RELATIVE_ALT]) + terrain_alt
    except KeyError:
        if make == "Sentera":
            logger.warning(
                "Relative altitude not found in XMP. Attempting to parse from session.txt file"
            )
            abs_alt = get_altitude_msl(image_path)
            session_alt = parse_session_alt(image_path)
            return abs_alt - session_alt
        else:
            raise ParsingError(
                "Couldn't parse relative altitude from xmp data. Sensor may not be supported"
            )


@get_if_needed("exif_data", getter=get_exif_data, getter_args=["image_path"])
def get_altitude_msl(image_path, exif_data=None):
    """
    Get the absolute altitude (meters above msl) of the sensor when the image was taken.

    :param image_path: the full path to the image
    :param exif_data: used internally for memoization. Not necessary to supply.
    :return: **altitude_msl** - the absolute altitude of the image in meters.
    :raises: ParsingError
    """
    try:
        return convert_to_float(exif_data["GPS GPSAltitude"])
    except KeyError:
        raise ParsingError("Couldn't parse altitude msl. Sensor might not be supported")


@get_if_needed("exif_data", getter=get_exif_data, getter_args=["image_path"])
@get_if_needed("xmp_data", getter=get_xmp_data, getter_args=["image_path"])
def get_gsd(
    image_path,
    exif_data=None,
    xmp_data=None,
    corrected_alt=None,
    use_calibrated_focal_length=False,
    alt_source="default",
    terrain_api_key=None,
    fallback=True,
):
    """
    Get the gsd of the image (in meters/pixel).

    :param image_path: the full path to the image
    :param exif_data: used internally for memoization. Not necessary to supply.
    :param xmp_data: used internally for memoization. Not necessary to supply.
    :param corrected_alt: corrected relative altitude (optional)
    :param use_calibrated_focal_length: enable to use calibrated focal length if available
    :param alt_source: See `get_relative_altitude()`
    :param terrain_api_key: Required if `alt_source` set to "terrain". API key to access google elevation api.
    :param fallback: Raise an error if the specified `alt_source` can't be accessed
    :return: **gsd** - the ground sample distance of the image in meters
    :raises: ParsingError
    """
    focal_length = get_focal_length_pixels(
        image_path, exif_data, xmp_data, use_calibrated_focal_length
    )
    if corrected_alt:
        alt = corrected_alt
    else:
        alt = get_relative_altitude(
            image_path,
            exif_data,
            xmp_data,
            alt_source,
            terrain_api_key=terrain_api_key,
            fallback=fallback,
        )

    if alt <= 0:
        raise ValueError("Parsed gsd is less than or equal to 0")

    return alt / focal_length


## Radiometry


@get_if_needed("exif_data", getter=get_exif_data, getter_args=["image_path"])
def get_autoexposure(image_path, exif_data=None):
    """
    Get the autoexposure value of the sensor when the image was taken.

    Autoexposure is derived from the integration time and gain of the sensor, which are stored in
    separate tags. This function retrieves those values and performs the calculation.

    :param image_path: the full path to the image
    :param exif_data: used internally for memoization. Not necessary to supply.
    :return: **autoexposure** - image autoexposure value
    :raises: ParsingError
    """
    try:
        iso = exif_data["EXIF ISOSpeedRatings"].values[0]
        integration_time = convert_to_float(exif_data["EXIF ExposureTime"])
    except KeyError:
        raise ParsingError(
            "Couldn't parse either ISO or exposure time. Sensor might not be supported"
        )

    return iso * integration_time


@get_if_needed("exif_data", getter=get_exif_data, getter_args=["image_path"])
@get_if_needed("xmp_data", getter=get_xmp_data, getter_args=["image_path"])
def get_ils(image_path, exif_data=None, xmp_data=None):
    """
    Get the ILS value of an image captured by a sensor with an ILS module.

    :param image_path: the full path to the image
    :param exif_data: used internally for memoization. Not necessary to supply.
    :param xmp_data: used internally for memoization. Not necessary to supply.
    :return: **ils** - ILS value of image, as a floating point number
    :raises: ParsingError
    """
    try:
        make, model = get_make_and_model(image_path, exif_data)
        xmp_tags = xmp.get_tags(make)
        return parse_seq(xmp_data[xmp_tags.ILS], float)
    except KeyError:
        raise ParsingError("Couldn't parse ILS value. Sensor might not be supported")


@get_if_needed("exif_data", getter=get_exif_data, getter_args=["image_path"])
@get_if_needed("xmp_data", getter=get_xmp_data, getter_args=["image_path"])
def get_wavelength_data(image_path, exif_data=None, xmp_data=None):
    """
    Get the central and FWHM wavelength values of an image.

    :param image_path: the full path to the image
    :param exif_data: used internally for memoization. Not necessary to supply.
    :param xmp_data: used internally for memoization. Not necessary to supply.
    :return: **central_wavelength** - central wavelength of each band, as a list of ints
    :return: **wavelength_fwhm** - wavelength fwhm of each band, as a list of ints
    :raises: ParsingError
    """
    try:
        make, model = get_make_and_model(image_path, exif_data)
        xmp_tags = xmp.get_tags(make)
        try:
            central_wavelength = parse_seq(xmp_data[xmp_tags.WAVELENGTH_CENTRAL], float)
            wavelength_fwhm = parse_seq(xmp_data[xmp_tags.WAVELENGTH_FWHM], float)
        except TypeError:
            central_wavelength = [float(xmp_data[xmp_tags.WAVELENGTH_CENTRAL])]
            wavelength_fwhm = [float(xmp_data[xmp_tags.WAVELENGTH_FWHM])]

        return central_wavelength, wavelength_fwhm
    except KeyError:
        raise ParsingError(
            "Couldn't parse wavelength data. Sensor might not be supported"
        )


@get_if_needed("exif_data", getter=get_exif_data, getter_args=["image_path"])
@get_if_needed("xmp_data", getter=get_xmp_data, getter_args=["image_path"])
def get_bandnames(image_path, exif_data=None, xmp_data=None):
    """
    Get the name of each band of an image.

    :param image_path: the full path to the image
    :param exif_data: used internally for memoization. Not necessary to supply.
    :param xmp_data: used internally for memoization. Not necessary to supply.
    :return: **band_names** - name of each band of image, as a list of strings
    :raises: ParsingError
    """
    try:
        make, model = get_make_and_model(image_path, exif_data)
        xmp_tags = xmp.get_tags(make)
        try:
            return parse_seq(xmp_data[xmp_tags.BANDNAME])
        except TypeError:
            return [xmp_data[xmp_tags.BANDNAME]]
    except KeyError:
        raise ParsingError("Couldn't parse bandnames. Sensor might not be supported")


@get_if_needed("exif_data", getter=get_exif_data, getter_args=["image_path"])
def get_lens_model(image_path, exif_data=None):
    """
    Get the Lens Model of an image from a Sentera Camera.

    :param image_path: the full path to the image
    :param exif_data: used internally for memoization. Not necessary to supply.
    :return: LensModel
    :raises: ParsingError
    """
    try:
        make, model = get_make_and_model(image_path, exif_data)
        if make == "Sentera":
            # Exif LensModel is Single and D4K. Images LensModel is 6x
            return (
                exif_data.get("Image LensModel").values
                if exif_data.get("Image LensModel")
                # will return KeyError if both are not found
                else exif_data["EXIF LensModel"].values
            )

        else:
            raise KeyError()

    except KeyError:
        raise ParsingError("Couldn't parse lens model. Sensor might not be supported")
