"""Extract metadata from exif and xmp tags in images."""

import logging
import os
import re
from datetime import datetime

import pytz
from timezonefinder import TimezoneFinder

from imgparse import xmp
from imgparse.decorators import get_if_needed
from imgparse.exceptions import ParsingError
from imgparse.getters import get_exif_data, get_xmp_data
from imgparse.pixel_pitches import PIXEL_PITCHES

logger = logging.getLogger(__name__)


def _convert_to_degrees(tag):
    """
    Convert the `exifread` GPS coordinate IfdTag object to degrees in float format.

    :param tag:
    :type tag: exifread.classes.IfdTag
    :rtype: float
    """
    degrees = _convert_to_float(tag, 0)
    minutes = _convert_to_float(tag, 1)
    seconds = _convert_to_float(tag, 2)

    return degrees + (minutes / 60.0) + (seconds / 3600.0)


def _convert_to_float(tag, index=0):
    """
    Convert `exifread` IfdTag object to float.

    :param tag:
    :param index:
    :return:
    """
    return float(tag.values[index].num) / float(tag.values[index].den)


def _parse_seq(tag, type_cast_func=None):
    """Parse an xml sequence."""
    seq = tag["rdf:Seq"]["rdf:li"]
    if isinstance(seq, list) and type_cast_func is not None:
        seq = [type_cast_func(item) for item in seq]
    return seq


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
        logger.error("Couldn't parse sensor version")
        raise ParsingError("Couldn't parse sensor version")

    return int(major), int(minor), int(patch)


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
        integration_time = _convert_to_float(exif_data["EXIF ExposureTime"])
    except KeyError:
        logger.error("Couldn't parse either ISO or exposure time")
        raise ParsingError("Couldn't parse either ISO or exposure time")

    return iso * integration_time


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
        logger.error("Couldn't parse image timestamp")
        raise ParsingError("Couldn't parse image timestamp")
    except ValueError:
        logger.error("Couldn't parse found timestamp with given format string")
        raise ParsingError("Couldn't parse found timestamp with given format string")

    make, model = get_make_and_model(image_path=image_path, exif_data=exif_data)
    if make == "Sentera":
        datetime_obj = pytz.utc.localize(datetime_obj)
    else:
        lat, lon = get_lat_lon(image_path=image_path, exif_data=exif_data)
        timezone = pytz.timezone(TimezoneFinder().timezone_at(lng=lon, lat=lat))
        datetime_obj = timezone.localize(datetime_obj)

    return datetime_obj


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
            return 1 / _convert_to_float(exif_data["EXIF FocalPlaneXResolution"]) / 100
        else:
            pixel_pitch = PIXEL_PITCHES[make][model]
    except KeyError:
        logger.error("Couldn't parse pixel pitch")
        raise ParsingError("Couldn't parse pixel pitch")

    return pixel_pitch


@get_if_needed("exif_data", getter=get_exif_data, getter_args=["image_path"])
@get_if_needed("xmp_data", getter=get_xmp_data, getter_args=["image_path"])
def get_camera_params(
    image_path, exif_data=None, xmp_data=None, use_calibrated_focal_length=False
):
    """
    Get the focal length and pixel pitch (in meters) of the sensor that took the image.

    :param image_path: the full path to the image (optional if `exif_data` provided)
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
        logger.error(
            "Couldn't find session.txt file in image directory: %s", imagery_dir
        )
        raise ParsingError("Couldn't find session.txt file in image directory")

    session_file = open(session_path, "r")
    session_alt = session_file.readline().split("\n")[0].split("=")[1]
    session_file.close()
    if not session_alt:
        logger.error(
            "Couldn't parse session altitude from session.txt for image: %s",
            imagery_dir,
        )
        raise ParsingError("Couldn't parse session altitude from session.txt")

    return float(session_alt)


@get_if_needed("exif_data", getter=get_exif_data, getter_args=["image_path"])
@get_if_needed("xmp_data", getter=get_xmp_data, getter_args=["image_path"])
def get_relative_altitude(
    image_path, exif_data=None, xmp_data=None, alt_source="default"
):
    """
    Get the relative altitude of the sensor above the ground (in meters) when the image was taken.

    If the image is from a Sentera sensor, will try to read the agl altitude from the xmp tags by default.  If
    image is from an older firmware version, this xmp tag will not exist, and will fall back to using the `session.txt`
    file associated with the image instead.

    :param image_path: the full path to the image
    :param exif_data: used internally for memoization. Not necessary to supply.
    :param xmp_data: used internally for memoization. Not necessary to supply.
    :param alt_source: for Sentera imagery, set to "session" to extract session agl alt, or "rlf" to use laser range finder
    :return: **relative_alt** - the relative altitude of the camera above the ground
    :raises: ParsingError
    """
    make, model = get_make_and_model(image_path, exif_data)
    xmp_tags = xmp.get_tags(make)
    if alt_source == "lrf":
        try:
            try:
                return float(xmp_data[xmp_tags.LRF_ALT])
            except KeyError:
                return float(xmp_data[xmp_tags.LRF_ALT2])
        except KeyError:
            logger.warning(
                "Altimeter calculated altitude not found in XMP. Defaulting to relative altitude."
            )

    try:
        return float(xmp_data[xmp_tags.RELATIVE_ALT])
    except KeyError:
        if make == "Sentera":
            logger.warning(
                "Relative altitude not found in XMP. Attempting to parse from session.txt file"
            )
            abs_alt = get_altitude_msl(image_path)
            session_alt = parse_session_alt(image_path)
            return abs_alt - session_alt
        else:
            logger.error(
                "Couldn't parse relative altitude from xmp data. Sensor may not be supported"
            )
            raise ParsingError(
                "Couldn't parse relative altitude from xmp data. Sensor may not be supported"
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
        logger.error("Couldn't parse lat/lon")
        raise ParsingError("Couldn't parse lat/lon")

    lat = _convert_to_degrees(gps_latitude)
    if gps_latitude_ref.values[0] != "N":
        lat = 0 - lat

    lon = _convert_to_degrees(gps_longitude)
    if gps_longitude_ref.values[0] != "E":
        lon = 0 - lon

    return lat, lon


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
        return _convert_to_float(exif_data["GPS GPSAltitude"])
    except KeyError:
        logger.error("Couldn't parse altitude msl")
        raise ParsingError("Couldn't parse altitude msl")


@get_if_needed("exif_data", getter=get_exif_data, getter_args=["image_path"])
@get_if_needed("xmp_data", getter=get_xmp_data, getter_args=["image_path"])
def get_roll_pitch_yaw(image_path, exif_data=None, xmp_data=None):
    """
    Get the orientation of the sensor (roll, pitch, yaw in degrees) when the image was taken.

    :param image_path: the full path to the image
    :param exif_data: used internally for memoization. Not necessary to supply.
    :param xmp_data: used internally for memoization. Not necessary to supply.
    :return: **roll, pitch, yaw** - the orientation (degrees) of the camera with respect to the NED frame
    :raises: ParsingError
    """
    make, model = get_make_and_model(image_path, exif_data)
    xmp_tags = xmp.get_tags(make)

    try:
        roll = float(xmp_data[xmp_tags.ROLL])
        pitch = float(xmp_data[xmp_tags.PITCH])
        yaw = float(xmp_data[xmp_tags.YAW])
        if make == "DJI" or make == "Hasselblad":
            # Bring pitch into aircraft pov
            pitch += 90
    except KeyError:
        logger.error("Couldn't parse roll/pitch/yaw")
        raise ParsingError("Couldn't parse roll/pitch/yaw")

    return roll, pitch, yaw


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
            make, model = get_make_and_model(image_path, exif_data=exif_data)
            xmp_tags = xmp.get_tags(make)
            return float(xmp_data[xmp_tags.FOCAL_LEN]) / 1000
        except KeyError:
            logger.warning(
                "Calibrated focal length not found in XMP. Defaulting to uncalibrated focal length"
            )

    try:
        return _convert_to_float(exif_data["EXIF FocalLength"]) / 1000
    except KeyError:
        logger.error("Couldn't parse the focal length")
        raise ParsingError("Couldn't parse the focal length")


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
        logger.error("Couldn't parse the make and model of the camera")
        raise ParsingError("Couldn't parse the make and model of the camera")


@get_if_needed("exif_data", getter=get_exif_data, getter_args=["image_path"])
def get_dimensions(image_path, exif_data=None):
    """
    Get the height and width (in pixels) of the image.

    :param image_path: the full path to the image
    :param exif_data: used internally for memoization. Not necessary to supply.
    :return: **height**, **width** - the height and width of the image
    :raises: ParsingError
    """
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
            raise ParsingError(f"Image format {ext} isn't supported for height/width")
    except KeyError:
        logger.error("Couldn't parse the height and width of the image")
        raise ParsingError("Couldn't parse the height and width of the image")


@get_if_needed("exif_data", getter=get_exif_data, getter_args=["image_path"])
@get_if_needed("xmp_data", getter=get_xmp_data, getter_args=["image_path"])
def get_gsd(
    image_path,
    exif_data=None,
    xmp_data=None,
    corrected_alt=None,
    use_calibrated_focal_length=False,
    alt_source="default",
):
    """
    Get the gsd of the image (in meters/pixel).

    :param image_path: the full path to the image
    :param exif_data: the exif dictionary for the image (optional to speed up processing)
    :param xmp_data: the XMP data of image, as a string dump of the original XML (optional to speed up processing)
    :param corrected_alt: corrected relative altitude (optional)
    :param use_calibrated_focal_length: enable to use calibrated focal length if available
    :param alt_source: Set to "lrf" to use laser range finder
    :return: **gsd** - the ground sample distance of the image in meters
    :raises: ParsingError
    """
    focal, pitch = get_camera_params(
        image_path, exif_data, xmp_data, use_calibrated_focal_length
    )
    if corrected_alt:
        alt = corrected_alt
    else:
        alt = get_relative_altitude(image_path, exif_data, xmp_data, alt_source)

    gsd = pitch * alt / focal
    if gsd <= 0:
        raise ValueError("Parsed gsd is less than or equal to 0")

    return gsd


@get_if_needed("exif_data", getter=get_exif_data, getter_args=["image_path"])
def get_wavelength_data(image_path=None, xmp_data=None):
    """
    Get the central and FWHM wavelength values of an image.

    :param image_path: the full path to the image
    :param xmp_data: used internally for memoization. Not necessary to supply.
    :return: **central_wavelength** - central wavelength of each band, as a list of ints
    :return: **wavelength_fwhm** - wavelength fwhm of each band, as a list of ints
    :raises: ParsingError
    """
    # TODO: Test
    try:
        make, model = get_make_and_model(image_path)
        xmp_tags = xmp.get_tags(make)
        central_wavelength = _parse_seq(xmp_data[xmp_tags.WAVELENGTH_CENTRAL], int)
        wavelength_fwhm = _parse_seq(xmp_data[xmp_tags.WAVELENGTH_FWHM], int)
        return central_wavelength, wavelength_fwhm
    except KeyError:
        logger.error("Couldn't parse wavelength data")
        raise ParsingError("Couldn't parse wavelength data")


# @get_if_needed("xmp_data", getter=get_xmp_data, getter_args=["image_path"])
# def get_bandnames(image_path=None, xmp_data=None):
#     """
#     Get the name of each band of an image.
#
#     :param image_path: the full path to the image (optional if `xmp_data` provided)
#     :param xmp_data: the XMP data of image, as a string dump of the original XML (optional to speed up processing)
#     :return: **band_names** -- name of each band of image, as a list of strings
#     :raises: ParsingError
#     """
#     # try:
#     #     band_names = xmp.find_multiple(xmp_data, [xmp.BNDNM, xmp.SEQ])
#     # except XMPTagNotFoundError:
#     #     logger.error("Couldn't parse bandnames")
#     #     raise ParsingError("Couldn't parse bandnames.")
#     #
#     # return band_names
#     # TODO: Bandnames not supported
#     raise ParsingError("Bandnames not supported")
#
#
@get_if_needed("xmp_data", getter=get_xmp_data, getter_args=["image_path"])
def get_ils(image_path=None, xmp_data=None, use_clear_channel=False):
    """
    Get the ILS value of an image captured by a sensor with an ILS module.

    :param image_path: the full path to the image (optional if `xmp_data` provided)
    :param xmp_data: the XMP data of image, as a string dump of the original XML (optional to speed up processing)
    :param use_clear_channel: if true, refer to the ILS clear channel value instead of the default
    :return: **ils** -- ILS value of image, as a floating point number
    :raises: ParsingError
    """
    # TODO: Support clear channel
    try:
        make, model = get_make_and_model(image_path)
        xmp_tags = xmp.get_tags(make)
        return float(_parse_seq(xmp_data[xmp_tags.ILS]))
    except KeyError:
        logger.error("Couldn't parse ILS value")
        raise ParsingError("Couldn't parse ILS value")
