"""
This module contains various functions that extract imagery information from exif and xmp tags in the
images.  Supports some DJI, some Hasselblad, and all Sentera sensors.

"""

import os
import logging
import exifread
import xmltodict
from imgparse.pixel_pitches import PIXEL_PITCHES

logger = logging.getLogger(__name__)


def _get_if_exist(dictionary, key):
    """
    Helper function for looking up a key in a dictionary.  If key doesn't exist, returns None.  Helps avoid
    key not found error handling.

    :param dictionary: dictionary of key/value pairs
    :param key: key to look up in provided dictionary
    :return: **value** - value associated with key, else None
    """
    if key in dictionary:
        return dictionary[key]

    return None


def _convert_to_degrees(tag):
    """
    Helper function to convert the `exifread` GPS coordinate IfdTag object to degrees in float format

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
    Helper function to convert `exifread` IfdTag object to float.

    :param tag:
    :param index:
    :return:
    """
    return float(tag.values[index].num) / float(tag.values[index].den)


def get_xmp_data(image_path):
    """
    Returns a dictionary of lookup keys/values for the xmp data of the provided image.

    :param image_path: full path to image to parse xmp from
    :return: **xmp_data** - a dictionary of lookup keys/values for image exif data.
    :raises: ValueError
    """
    if not image_path or not os.path.isfile(image_path):
        logger.error("Image doesn't exist.  Couldn't read xmp data for image: %s", image_path)
        raise ValueError("Image doesn't exist. Couldn't read xmp data")

    with open(image_path, "rb") as file:
        img = str(file.read())
        file.close()

    xmp_start = img.find('<x:xmpmeta')
    xmp_end = img.find('</x:xmpmeta')
    if xmp_start != xmp_end:
        xmp = img[xmp_start:xmp_end + 12].replace("\\n", "\n")
        xmp_dict = xmltodict.parse(xmp)
        return xmp_dict['x:xmpmeta']

    logger.error("Couldn't read xmp data for image: %s", image_path)
    raise ValueError("Couldn't read xmp data from image.")


def get_exif_data(image_path):
    """
    Returns a dictionary of lookup keys/values for the exif data of the provided image.  This dictionary is an optional
    argument for the various ``imgparse`` functions to speed up processing by only reading the exif data once per image.
    Otherwise this function is used internally for ``imgparse`` functions to extract the needed exif data.

    :param image_path: full path to image to parse exif from
    :return: **exif_data** - a dictionary of lookup keys/values for image exif data.
    :raises: ValueError
    """
    if not image_path or not os.path.isfile(image_path):
        logger.error("Image doesn't exist.  Can't read exif data for image: %s", image_path)
        raise ValueError("Image doesn't exist. Couldn't read exif data.")

    file = open(image_path, 'rb')
    exif_data = exifread.process_file(file)
    file.close()

    if not exif_data:
        raise ValueError("Couldn't read exif data for image.")

    return exif_data


def get_camera_params(image_path=None, exif_data=None):
    """
    Returns the focal length and pixel pitch of the sensor that took the image, extracted
    from the image's exif tags.  DJI doesn't store the pixel pitch in the exif tags, so
    that is found in a lookup table.  See `pixel_pitches.py` to see which DJI sensor models are supported.
    To support new sensors, add the model name and associated pixel pitch to the **DJI_PIXEL_PITCH** dictionary at the
    top of `pixel_pitches.py`.

    :param image_path: the full path to the image (optional if `exif_data` provided)
    :param exif_data: the exif dictionary for the image (optional to speed up processing)
    :return: **focal_length, pixel_pitch** - the camera parameters in meters
    :raises: ValueError
    """
    make, model = get_make_and_model(image_path, exif_data)
    focal_length = get_focal_length(image_path, exif_data)
    pixel_pitch = None

    if make == "Sentera":
        pixel_pitch = get_sentera_pixel_pitch(image_path, exif_data)
    else:
        pixel_pitch_dict = _get_if_exist(PIXEL_PITCHES, make)
        if pixel_pitch_dict:
            pixel_pitch = _get_if_exist(pixel_pitch_dict, model)

    if focal_length and pixel_pitch:
        return focal_length, pixel_pitch

    logger.error("Couldn't parse camera parameters")
    raise ValueError("Couldn't parse camera parameters.\nCamera make/model may not exist in pixel_pitches.py")


def get_relative_altitude(image_path, exif_data=None):
    """
    Returns the relative altitude of the camera above the ground that is stored in the image exif
    and xmp tags.  If image is from a Sentera sensor, `session.txt` must be in the image's directory
    in order for the relative altitude to be calculated.

    .. note::

        Unlike some other functions in ``imgparse``, `image_path` is mandatory whether or not `exif_data` is provided.

    :param image_path: the full path to the image
    :param exif_data: the exif dictionary for the image (optional to speed up processing)
    :return: **relative_alt** - the relative altitude of the camera above the ground
    :raises: ValueError
    """
    make, model = get_make_and_model(image_path, exif_data)
    if make == 'Sentera':
        abs_alt = get_altitude_msl(image_path)
        session_alt = parse_session_alt(image_path)
        rel_alt = abs_alt - session_alt
    else:
        xmp_dict = get_xmp_data(image_path)
        try:
            alt_str = xmp_dict['rdf:RDF']['rdf:Description']['@drone-dji:RelativeAltitude']
            rel_alt = float(alt_str)
        except KeyError:
            raise ValueError("Couldn't parse relative altitude from xmp data.  Camera type may not be supported.")

    if not rel_alt:
        logger.error("Couldn't parse relative altitude")
        raise ValueError("Couldn't parse relative altitude")

    return rel_alt


def get_lat_lon(image_path=None, exif_data=None):
    """
    Returns the latitude and longitude of where the image was taken, stored in the image's
    exif tags.

    :param image_path: the full path to the image (optional if `exif_data` provided)
    :param exif_data: the exif dictionary for the image (optional to speed up processing)
    :return: **latitude, longitude** - the location of where the image was taken
    :raises: ValueError
    """
    if not exif_data:
        exif_data = get_exif_data(image_path)

    lat = None
    lon = None

    gps_latitude = _get_if_exist(exif_data, 'GPS GPSLatitude')
    gps_latitude_ref = _get_if_exist(exif_data, 'GPS GPSLatitudeRef')
    gps_longitude = _get_if_exist(exif_data, 'GPS GPSLongitude')
    gps_longitude_ref = _get_if_exist(exif_data, 'GPS GPSLongitudeRef')

    if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
        lat = _convert_to_degrees(gps_latitude)
        if gps_latitude_ref.values[0] != 'N':
            lat = 0 - lat

        lon = _convert_to_degrees(gps_longitude)
        if gps_longitude_ref.values[0] != 'E':
            lon = 0 - lon

    if lat is None or lon is None:
        logger.error("Couldn't extract lat/lon")
        raise ValueError("Couldn't extract lat/lon")

    return lat, lon


def get_altitude_msl(image_path=None, exif_data=None):
    """
    Parses the absolute altitude of the image.

    :param image_path: the full path to the image (optional if `exif_data` provided)
    :param exif_data: the exif dictionary for the image (optional to speed up processing)
    :return: **altitude_msl** - the absolute altitude of the image in meters.
    :raises: ValueError
    """
    if not exif_data:
        exif_data = get_exif_data(image_path)

    alt_tag = _get_if_exist(exif_data, 'GPS GPSAltitude')
    if alt_tag:
        return _convert_to_float(alt_tag)

    logger.error("Couldn't extract altitude msl")
    raise ValueError("Couldn't extract altitude msl")


def get_roll_pitch_yaw(image_path):
    """
    Returns the latitude and longitude of where the image was taken, stored in the image's
    exif tags.

    :param image_path: the full path to the image (optional if `exif_data` provided)
    :param exif_data: the exif dictionary for the image (optional to speed up processing)
    :return: **roll, pitch, yaw** - the orientation (degrees) of the camera with respect to the NED frame
    :raises: ValueError
    """
    roll = None
    pitch = None
    yaw = None

    make, model = get_make_and_model(image_path)
    xmp_dict = get_xmp_data(image_path)
    if make == 'Sentera':
        roll_str = xmp_dict['rdf:RDF']['rdf:Description']['@Camera:Roll']
        roll = float(roll_str)
        pitch_str = xmp_dict['rdf:RDF']['rdf:Description']['@Camera:Pitch']
        pitch = float(pitch_str)
        yaw_str = xmp_dict['rdf:RDF']['rdf:Description']['@Camera:Yaw']
        yaw = float(yaw_str)
    else:
        try:
            roll_str = xmp_dict['rdf:RDF']['rdf:Description']['@drone-dji:FlightRollDegree']
            roll = float(roll_str)
            pitch_str = xmp_dict['rdf:RDF']['rdf:Description']['@drone-dji:FlightPitchDegree']
            pitch = float(pitch_str)
            yaw_str = xmp_dict['rdf:RDF']['rdf:Description']['@drone-dji:FlightYawDegree']
            yaw = float(yaw_str)
        except KeyError:
            raise ValueError("Couldn't parse euler angles from xmp data.  Camera type may not be supported.")

    if roll is None or pitch is None or yaw is None:
        logger.error("Couldn't extract roll/pitch/yaw")
        raise ValueError("Couldn't extract roll/pitch/yaw")

    return roll, pitch, yaw


def get_focal_length(image_path=None, exif_data=None):
    """
    Parses the focal length of the camera from the image.

    :param image_path: the full path to the image (optional if `exif_data` provided)
    :param exif_data: the exif dictionary for the image (optional to speed up processing)
    :return: **focal_length** - the focal length of the camera in meters
    :raises: ValueError
    """
    if not exif_data:
        exif_data = get_exif_data(image_path)

    fl_tag = _get_if_exist(exif_data, 'EXIF FocalLength')
    if fl_tag:
        return _convert_to_float(fl_tag) / 1000

    logger.error("Couldn't parse the focal length")
    raise ValueError("Couldn't parse the focal length")


def get_make_and_model(image_path=None, exif_data=None):
    """
    Parses the make and model of the camera from the image.

    :param image_path: the full path to the image (optional if `exif_data` provided)
    :param exif_data: the exif dictionary for the image (optional to speed up processing)
    :return: **make**, **model** - the make and model of the camera
    :raises: ValueError
    """
    if not exif_data:
        exif_data = get_exif_data(image_path)

    make_tag = _get_if_exist(exif_data, 'Image Make')
    model_tag = _get_if_exist(exif_data, 'Image Model')
    if make_tag and model_tag:
        return make_tag.values, model_tag.values

    logger.error("Couldn't parse the make and model of the camera")
    raise ValueError("Couldn't parse the make and model of the camera")


def get_sentera_pixel_pitch(image_path=None, exif_data=None):
    """
    Parses the pixel pitch from Sentera cameras.  Won't parse pixel pitch for non-Sentera cameras.

    :param image_path: the full path to the image (optional if `exif_data` provided)
    :param exif_data: the exif dictionary for the image (optional to speed up processing)
    :return: **pixel_pitch** - the pixel_pitch of the camera
    :raises: ValueError
    """
    if not exif_data:
        exif_data = get_exif_data(image_path)

    focal_res_tag = _get_if_exist(exif_data, 'EXIF FocalPlaneXResolution')
    if focal_res_tag:
        return 1 / _convert_to_float(focal_res_tag) / 100

    logger.error("Couldn't parse the pixel pitch")
    raise ValueError("Couldn't parse the pixel pitch")


def parse_session_alt(image_path):
    """
    Parses the session ground altitude from `session.txt`.  Used for Sentera cameras since relative altitude isn't
    stored in exif or xmp tags, and instead the session ground altitude is written as a text file that needs to be read.
    The `session.txt` must be in the same directory as the image in order to be read.

    :param image_path: the full path to the image
    :return: **pixel_pitch** - the pixel_pitch of the camera
    :raises: ValueError
    """
    imagery_dir = os.path.dirname(image_path)
    session_path = os.path.join(imagery_dir, "session.txt")
    if not os.path.isfile(session_path):
        logger.error("Couldn't find session.txt file in image directory: %s", imagery_dir)
        raise ValueError("Couldn't find session.txt file in image directory")

    session_file = open(session_path, "r")
    session_alt = session_file.readline().split("\n")[0].split("=")[1]
    session_file.close()
    if session_alt:
        return float(session_alt)

    logger.error("Couldn't parse session altitude from session.txt for image: %s", imagery_dir)
    raise ValueError("Couldn't parse session altitude from session.txt")


def get_gsd(image_path, exif_data=None):
    """
    Parses the necessary metadata and calculates the gsd of the image.

    .. note::

        Unlike some other functions in ``imgparse``, `image_path` is mandatory whether or not `exif_data` is provided.

    :param image_path: the full path to the image
    :param exif_data: the exif dictionary for the image (optional to speed up processing)
    :return: **gsd** - the ground sample distance of the image in meters
    :raises: ValueError
    """

    focal, pitch = get_camera_params(image_path, exif_data)
    alt = get_relative_altitude(image_path, exif_data)

    return pitch * alt / focal
