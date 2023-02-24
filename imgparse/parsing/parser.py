"""Extract metadata from exif and xmp tags in images."""

import logging
import os
import re
from datetime import datetime

import pytz

from imgparse import xmp
from imgparse.decorators import get_if_needed
from imgparse.exceptions import ParsingError
from imgparse.getters import get_exif_data, get_xmp_data
from imgparse.pixel_pitches import PIXEL_PITCHES
from imgparse.rotations import Euler, apply_rotational_offset
from imgparse.util import convert_to_degrees, convert_to_float

logger = logging.getLogger(__name__)


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

    return int(major), int(minor), int(patch)


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
        datetime_obj = datetime.strptime(
            exif_data["EXIF DateTimeOriginal"].values, format_string
        )
    except KeyError:
        raise ParsingError(
            "Couldn't parse image timestamp. Sensor might not be supported"
        )
    except ValueError:
        raise ParsingError("Couldn't parse found timestamp with given format string")

    make, model = get_make_and_model(image_path, exif_data)
    if make == "Sentera":
        datetime_obj = pytz.utc.localize(datetime_obj)
    else:
        lat, lon = get_lat_lon(image_path, exif_data)
        try:
            from timezonefinder import TimezoneFinder

            timezone = pytz.timezone(TimezoneFinder().timezone_at(lng=lon, lat=lat))
        except ImportError:
            logger.warning(
                "Module timezonefinder is required for retrieving timestamps from DJI sensors."
                "Please execute `poetry install -E dji_timestamps` to install this module."
            )
            raise

        datetime_obj = timezone.localize(datetime_obj)

    return datetime_obj


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
            return (
                exif_data["EXIF ExifImageLength"].values[0],
                exif_data["EXIF ExifImageWidth"].values[0],
            )
        elif ext in [".tif", ".tiff"]:
            return (
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
                return (7000, 9344)
            elif model.startswith("21214-"):
                # 6X RGB
                return (3888, 5184)
        raise ParsingError(
            "Couldn't parse the height and width of the image. Sensor might not be supported"
        )


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

    return lat, lon


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
        roll = float(xmp_data[xmp_tags.ROLL])
        pitch = float(xmp_data[xmp_tags.PITCH])
        yaw = float(xmp_data[xmp_tags.YAW])

        if standardize:
            if make == "DJI" or make == "Hasselblad":
                # DJI describes orientation in terms of the gimbal reference frame
                # Thus camera pointing down is pitch = -90
                # Apply pitch rotation of +90 to convert to standard reference frame
                roll, pitch, yaw = apply_rotational_offset(
                    Euler(roll, pitch, yaw), Euler(0, 90, 0)
                )
    except KeyError:
        raise ParsingError(
            "Couldn't parse roll/pitch/yaw. Sensor might not be supported"
        )

    return roll, pitch, yaw


def _get_pixel_pitch_m(image_path, exif_data):
    """
    Get pixel pitch (in meters) of the sensor that took the image.

    Non-Sentera cameras don't store the pixel pitch in the exif tags, so that is found in a lookup table.  See
    `pixel_pitches.py` to check which non-Sentera sensor models are supported and to add support for new sensors.
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


def _get_focal_length_m(
    image_path, exif_data=None, xmp_data=None, use_calibrated=False
):
    """
    Get the focal length (in meters) of the sensor that took the image.
    """
    if use_calibrated:
        try:
            make, model = get_make_and_model(image_path, exif_data)
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
def get_focal_length(image_path, exif_data=None, xmp_data=None, calibrated_fl=False):
    """
    Get the focal length and pixel pitch (in meters) of the sensor that took the image.

    :param image_path: the full path to the image
    :param exif_data: used internally for memoization. Not necessary to supply.
    :param xmp_data: used internally for memoization. Not necessary to supply.
    :param calibrated_fl: enable to use calibrated focal length if available
    :return: **focal_length, pixel_pitch** - the camera parameters in meters
    :raises: ParsingError
    """
    focal_length_m = _get_focal_length_m(image_path, exif_data, xmp_data, calibrated_fl)
    pixel_pitch_m = _get_pixel_pitch_m(image_path, exif_data)

    return focal_length_m / pixel_pitch_m
