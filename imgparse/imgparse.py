"""Extract metadata from exif and xmp tags in images."""

import logging
import os
from datetime import datetime

import imgparse.xmp as xmp
from imgparse.decorators import cache, get_if_needed
from imgparse.pixel_pitches import PIXEL_PITCHES
from imgparse.xmp import XMPTagNotFoundError

logger = logging.getLogger(__name__)

cache_exif_and_xmp = cache("exif_data", "xmp_data", using="image_path")


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


@get_if_needed("xmp_data", using="image_path")
@cache_exif_and_xmp
def get_ils(image_path=None, xmp_data=None):
    """
    Get the ILS value of an image taken with a Sentera 6X sensor with an ILS module.

    This function will always raise an exception if called on XMP data from any sensor other than a 6X with
    an included ILS module.

    :param image_path: the full path to the image (optional if `xmp_data` provided)
    :param xmp_data: the XMP data of image, as a string dump of the original XML (optional to speed up processing)
    :return: **ils** -- ILS value of image, as a floating point number
    :raises: XMPTagNotFoundError
    """
    try:
        ils = float(xmp.find(xmp_data, [xmp.ILS, xmp.SEQ]))

    except XMPTagNotFoundError:
        logger.error("Couldn't parse ILS value")
        raise XMPTagNotFoundError(
            "Couldn't parse ILS value. ILS will only be present if the sensor is a Sentera 6X "
            "with an ILS module."
        )

    return ils


@get_if_needed("exif_data", using="image_path")
@cache_exif_and_xmp
def get_autoexposure(image_path=None, exif_data=None):
    """
    Get the autoexposure value of the sensor when the image was taken.

    Autoexposure is derived from the integration time and gain of the sensor, which are stored in
    separate tags. This function retrieves those values and performs the calculation.

    :param image_path: the full path to the image (optional if `exif_data` provided)
    :param exif_data: the exif dictionary for the image (optional to speed up processing)
    :return: **autoexposure** - image autoexposure value
    """
    try:
        iso = exif_data["EXIF ISOSpeedRatings"].values[0] / 100
        integration_time = _convert_to_float(exif_data["EXIF ExposureTime"])
    except KeyError:
        logger.error("Couldn't parse either ISO or exposure time.")
        raise ValueError("Couldn't parse either ISO or exposure time.")

    autoexposure = iso * integration_time
    return autoexposure


@get_if_needed("exif_data", using="image_path")
@cache_exif_and_xmp
def get_timestamp(image_path=None, exif_data=None, format_string="%Y:%m:%d %H:%M:%S"):
    """
    Get the time stamp of an image and parse it into a `datetime` object with the given format string.

    If originating from a Sentera or DJI sensor, the format of the tag will likely be that of the default input.
    However, other sensors may store timestamps in other formats.

    :param image_path: the full path to the image (optional if `exif_data` provided)
    :param exif_data: the exif dictionary for the image (optional to speed up processing)
    :param format_string: Format code, as a string, to be used to parse the image timestamp.
    :return: **datetime_obj**: Parsed timestamp, in the format specified by the input format string.
    """
    try:
        datetime_obj = datetime.strptime(
            exif_data["EXIF DateTimeOriginal"].values, format_string
        )
    except KeyError:
        logger.error("Couldn't determine image timestamp.")
        raise ValueError("Couldn't determine image timestamp.")
    except ValueError:
        logger.error("Couldn't parse found timestamp with given format string.")
        raise ValueError("Couldn't parse found timestamp with given format string.")

    return datetime_obj


@get_if_needed("exif_data", using="image_path")
@cache_exif_and_xmp
def get_pixel_pitch(image_path=None, exif_data=None):
    """
    Get pixel pitch (in meters) of the sensor that took the image.

    Non-Sentera cameras don't store the pixel pitch in the exif tags, so that is found in a lookup table.  See
    `pixel_pitches.py` to check which non-Sentera sensor models are supported and to add support for new sensors.

    :param image_path: the full path to the image (optional if `exif_data` provided)
    :param exif_data: the exif dictionary for the image (optional to speed up processing)
    :return: **pixel_pitch** - the pixel pitch of the camera in meters
    :raises: ValueError
    """
    make, model = get_make_and_model(image_path, exif_data)
    if make == "Sentera":
        pixel_pitch = _get_sentera_pixel_pitch(image_path, exif_data)
    else:
        try:
            pixel_pitch = PIXEL_PITCHES[make][model]
        except KeyError:
            logger.error("Couldn't determine pixel pitch")
            raise ValueError(
                "Couldn't determine pixel pitch.\nCamera make/model may not exist in pixel_pitches.py"
            )

    return pixel_pitch


@get_if_needed("exif_data", using="image_path")
@cache_exif_and_xmp
def get_camera_params(image_path=None, exif_data=None):
    """
    Get the focal length and pixel pitch (in meters) of the sensor that took the image.

    :param image_path: the full path to the image (optional if `exif_data` provided)
    :param exif_data: the exif dictionary for the image (optional to speed up processing)
    :return: **focal_length, pixel_pitch** - the camera parameters in meters
    :raises: ValueError
    """
    focal_length = get_focal_length(image_path, exif_data)
    pixel_pitch = get_pixel_pitch(image_path, exif_data)

    return focal_length, pixel_pitch


@get_if_needed("exif_data", "xmp_data", using="image_path")
@cache_exif_and_xmp
def get_relative_altitude(image_path, exif_data=None, xmp_data=None, session_alt=False):
    """
    Get the relative altitude of the sensor above the ground (in meters) when the image was taken.

    If the image is from a Sentera sensor, will try to read the agl altitude from the xmp tags by default.  If
    image is from an older firmware version, this xmp tag will not exist, and will fall back to using the `session.txt`
    file associated with the image instead.  This `session.txt` must be in the image's directory for older firmware
    versions, or if the ``session_alt`` flag is enabled to specifically use the session altitude.

    .. note::

        Unlike some other functions in ``imgparse``, `image_path` is mandatory whether or not `exif_data` is provided.

    :param image_path: the full path to the image
    :param exif_data: the exif dictionary for the image (optional to speed up processing)
    :param xmp_data: the XMP data of image, as a string dump of the original XML (optional to speed up processing)
    :param session_alt: enable to extract the session agl altitude instead of xmp agl altitude for Sentera imagery
    :return: **relative_alt** - the relative altitude of the camera above the ground
    :raises: XMPTagNotFoundError
    """

    def _fallback_to_session(image_path):
        abs_alt = get_altitude_msl(image_path)
        session_alt = parse_session_alt(image_path)
        return abs_alt - session_alt

    make, model = get_make_and_model(image_path, exif_data)
    if make == "Sentera":
        if not session_alt:
            try:
                rel_alt = float(xmp.find(xmp_data, [xmp.Sentera.RELATIVE_ALT]))
            except XMPTagNotFoundError:
                logger.warning(
                    "Relative altitude not found in XMP. Attempting to parse from session.txt file."
                )
                rel_alt = _fallback_to_session(image_path)
        else:
            rel_alt = _fallback_to_session(image_path)
    else:
        try:
            rel_alt = float(xmp.find(xmp_data, [xmp.DJI.RELATIVE_ALT]))
        except XMPTagNotFoundError:
            raise XMPTagNotFoundError(
                "Couldn't parse relative altitude from xmp data.  Camera type may not be supported."
            )

    return rel_alt


@get_if_needed("exif_data", using="image_path")
@cache_exif_and_xmp
def get_lat_lon(image_path=None, exif_data=None):
    """
    Get the latitude and longitude of the sensor when the image was taken.

    :param image_path: the full path to the image (optional if `exif_data` provided)
    :param exif_data: the exif dictionary for the image (optional to speed up processing)
    :return: **latitude, longitude** - the location of where the image was taken
    :raises: ValueError
    """
    try:
        gps_latitude = exif_data["GPS GPSLatitude"]
        gps_latitude_ref = exif_data["GPS GPSLatitudeRef"]
        gps_longitude = exif_data["GPS GPSLongitude"]
        gps_longitude_ref = exif_data["GPS GPSLongitudeRef"]
    except KeyError:
        logger.error("Couldn't extract lat/lon")
        raise ValueError("Couldn't extract lat/lon")

    lat = _convert_to_degrees(gps_latitude)
    if gps_latitude_ref.values[0] != "N":
        lat = 0 - lat

    lon = _convert_to_degrees(gps_longitude)
    if gps_longitude_ref.values[0] != "E":
        lon = 0 - lon

    return lat, lon


@get_if_needed("exif_data", using="image_path")
@cache_exif_and_xmp
def get_altitude_msl(image_path=None, exif_data=None):
    """
    Get the absolute altitude (meters above msl) of the sensor when the image was taken.

    :param image_path: the full path to the image (optional if `exif_data` provided)
    :param exif_data: the exif dictionary for the image (optional to speed up processing)
    :return: **altitude_msl** - the absolute altitude of the image in meters.
    :raises: ValueError
    """
    try:
        return _convert_to_float(exif_data["GPS GPSAltitude"])
    except KeyError:
        logger.error("Couldn't extract altitude msl")
        raise ValueError("Couldn't extract altitude msl")


@get_if_needed("exif_data", "xmp_data", using="image_path")
@cache_exif_and_xmp
def get_roll_pitch_yaw(image_path=None, exif_data=None, xmp_data=None):
    """
    Get the orientation of the sensor (roll, pitch, yaw in degrees) when the image was taken.

    .. note::

        Only Sentera and DJI sensors are supported for this function right now.

    :param image_path: the full path to the image (optional if `exif_data` provided)
    :param exif_data: the exif dictionary for the image (optional to speed up processing)
    :param xmp_data: the XMP data of image, as a string dump of the original XML (optional to speed up processing)
    :return: **roll, pitch, yaw** - the orientation (degrees) of the camera with respect to the NED frame
    :raises: XMPTagNotFoundError
    """
    make, model = get_make_and_model(image_path, exif_data)

    try:
        if make == "Sentera":
            roll = float(xmp.find(xmp_data, [xmp.Sentera.ROLL]))
            pitch = float(xmp.find(xmp_data, [xmp.Sentera.PITCH]))
            yaw = float(xmp.find(xmp_data, [xmp.Sentera.YAW]))
        elif make == "DJI":
            roll = float(xmp.find(xmp_data, [xmp.DJI.ROLL]))
            pitch = float(xmp.find(xmp_data, [xmp.DJI.PITCH]))
            # Bring pitch into aircraft pov
            pitch += 90
            yaw = float(xmp.find(xmp_data, [xmp.DJI.YAW]))
        else:
            raise XMPTagNotFoundError()
    except XMPTagNotFoundError:
        logger.error(
            "Couldn't extract roll/pitch/yaw.  Only Sentera and DJI sensors are supported right now"
        )
        raise XMPTagNotFoundError(
            "Couldn't extract roll/pitch/yaw.  Only Sentera and DJI sensors are supported right now"
        )

    return roll, pitch, yaw


@get_if_needed("exif_data", using="image_path")
@cache_exif_and_xmp
def get_focal_length(image_path=None, exif_data=None):
    """
    Get the focal length (in meters) of the sensor that took the image.

    :param image_path: the full path to the image (optional if `exif_data` provided)
    :param exif_data: the exif dictionary for the image (optional to speed up processing)
    :return: **focal_length** - the focal length of the camera in meters
    :raises: ValueError
    """
    try:
        return _convert_to_float(exif_data["EXIF FocalLength"]) / 1000
    except KeyError:
        logger.error("Couldn't parse the focal length")
        raise ValueError("Couldn't parse the focal length")


@get_if_needed("exif_data", using="image_path")
@cache_exif_and_xmp
def get_make_and_model(image_path=None, exif_data=None):
    """
    Get the make and model of the sensor that took the image.

    :param image_path: the full path to the image (optional if `exif_data` provided)
    :param exif_data: the exif dictionary for the image (optional to speed up processing)
    :return: **make**, **model** - the make and model of the camera
    :raises: ValueError
    """
    try:
        return exif_data["Image Make"].values, exif_data["Image Model"].values
    except KeyError:
        logger.error("Couldn't parse the make and model of the camera")
        raise ValueError("Couldn't parse the make and model of the camera")


@get_if_needed("exif_data", using="image_path")
@cache_exif_and_xmp
def get_dimensions(image_path=None, exif_data=None):
    """
    Get the height and width (in pixels) of the image.

    :param image_path: the full path to the image (optional if `exif_data` provided)
    :param exif_data: the exif dictionary for the image (optional to speed up processing)
    :return: **height**, **width** - the height and width of the image
    :raises: ValueError
    """
    try:
        return (
            exif_data["EXIF ExifImageLength"].values[0],
            exif_data["EXIF ExifImageWidth"].values[0],
        )
    except KeyError:
        logger.error("Couldn't parse the height and width of the image")
        raise ValueError("Couldn't parse the height and width of the image")


@get_if_needed("exif_data", using="image_path")
@cache_exif_and_xmp
def _get_sentera_pixel_pitch(image_path=None, exif_data=None):
    """
    Get the pixel pitch (in meters) from Sentera sensors.

    Won't parse pixel pitch for non-Sentera cameras.

    :param image_path: the full path to the image (optional if `exif_data` provided)
    :param exif_data: the exif dictionary for the image (optional to speed up processing)
    :return: **pixel_pitch** - the pixel_pitch of the camera
    :raises: ValueError
    """
    try:
        return 1 / _convert_to_float(exif_data["EXIF FocalPlaneXResolution"]) / 100
    except KeyError:
        logger.error("Couldn't parse the pixel pitch")
        raise ValueError("Couldn't parse the pixel pitch")


def parse_session_alt(image_path):
    """
    Get the session ground altitude (meters above msl) from a `session.txt` file.

    Used for Sentera cameras since relative altitude isn't stored in exif or xmp tags, and instead the session ground
    altitude is written as a text file that needs to be read.  The `session.txt` must be in the same directory as the
    image in order to be read.

    :param image_path: the full path to the image
    :return: **ground_alt** - the session ground altitude, used to calculate relative altitude.
    :raises: ValueError
    """
    imagery_dir = os.path.dirname(image_path)
    session_path = os.path.join(imagery_dir, "session.txt")
    if not os.path.isfile(session_path):
        logger.error(
            "Couldn't find session.txt file in image directory: %s", imagery_dir
        )
        raise ValueError("Couldn't find session.txt file in image directory")

    session_file = open(session_path, "r")
    session_alt = session_file.readline().split("\n")[0].split("=")[1]
    session_file.close()
    if session_alt:
        return float(session_alt)

    logger.error(
        "Couldn't parse session altitude from session.txt for image: %s", imagery_dir
    )
    raise ValueError("Couldn't parse session altitude from session.txt")


@get_if_needed("exif_data", "xmp_data", using="image_path")
@cache_exif_and_xmp
def get_gsd(image_path, exif_data=None, xmp_data=None, corrected_alt=None):
    """
    Get the gsd of the image (in meters/pixel).

    .. note::

        Unlike some other functions in ``imgparse``, `image_path` is mandatory whether or not `exif_data` is provided.

    :param image_path: the full path to the image
    :param exif_data: the exif dictionary for the image (optional to speed up processing)
    :param xmp_data: the XMP data of image, as a string dump of the original XML (optional to speed up processing)
    :param corrected_alt: corrected relative altitude (optional, and only available
                                                        if supplied from an analytics metadata CSV)
    :return: **gsd** - the ground sample distance of the image in meters
    :raises: ValueError
    """
    focal, pitch = get_camera_params(image_path, exif_data)
    if corrected_alt:
        alt = corrected_alt
    else:
        alt = get_relative_altitude(image_path, exif_data, xmp_data)

    return pitch * alt / focal
