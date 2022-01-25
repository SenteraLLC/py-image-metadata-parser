import logging

from imgparse.decorators import get_if_needed
from imgparse.getters import get_exif_data, get_xmp_data
from imgparse.exceptions import ParsingError
from imgparse import parsers

logger = logging.getLogger(__name__)


@get_if_needed("exif_data", getter=get_exif_data, getter_args=["image_path"])
@get_if_needed("xmp_data", getter=get_xmp_data, getter_args=["image_path"])
def parser_factory(image_path, exif_data=None, xmp_data=None):
    make, model = get_make_and_model(image_path, exif_data)
    if make == "Sentera":
        return parsers.SenteraParser(exif_data, xmp_data, make, model, image_path)
    elif make == "Sony":
        return parsers.SonyParser(exif_data, xmp_data, make, model, image_path)
    elif make == "DJI":
        return parsers.DJIParser(exif_data, xmp_data, make, model, image_path)
    elif make == "Hasselblad":
        return parsers.HasselbladParser(exif_data, xmp_data, make, model, image_path)
    else:
        return parsers.Parser(exif_data, xmp_data, make, model, image_path)


@get_if_needed("exif_data", getter=get_exif_data, getter_args=["image_path"])
def get_make_and_model(image_path, exif_data=None):
    try:
        return exif_data["Image Make"].values, exif_data["Image Model"].values
    except KeyError:
        raise ParsingError("Couldn't parse the make and model of the camera")


def get_firmware_version(image_path):
    try:
        return parser_factory(image_path).get_firmware_version()
    except KeyError:
        raise ParsingError("Couldn't parse sensor version")


def get_autoexposure(image_path):
    try:
        return parser_factory(image_path).get_autoexposure()
    except KeyError:
        raise ParsingError("Couldn't parse autoexposure")


def get_timestamp(image_path, format_string=None):
    try:
        parser = parser_factory(image_path)
        if format_string is not None:
            return parser.get_timestamp(format_string)
        else:
            return parser.get_timestamp()
    except KeyError:
        raise ParsingError("Couldn't parse image timestamp")


def get_lat_lon(image_path):
    try:
        return parser_factory(image_path).get_lat_lon()
    except KeyError:
        raise ParsingError("Couldn't parse lat/lon")


def get_altitude_msl(image_path):
    try:
        return parser_factory(image_path).get_altitude_msl()
    except KeyError:
        raise ParsingError("Couldn't parse altitude msl")


def get_roll_pitch_yaw(image_path):
    try:
        return parser_factory(image_path).get_roll_pitch_yaw()
    except KeyError:
        raise ParsingError("Couldn't parse roll/pitch/yaw")


def get_pixel_pitch(image_path):
    try:
        return parser_factory(image_path).get_pixel_pitch()
    except KeyError:
        raise ParsingError(f"Couldn't parse pixel pitch")


def get_focal_length(image_path, use_calibrated=False):
    try:
        return parser_factory(image_path).get_focal_length(use_calibrated)
    except KeyError:
        raise ParsingError(f"Couldn't parse focal length")


def get_camera_params(image_path, use_calibrated=False):
    parser = parser_factory(image_path)
    return parser.get_focal_length(use_calibrated), parser.get_pixel_pitch()


def get_dimensions(image_path):
    try:
        return parser_factory(image_path).get_dimensions()
    except KeyError:
        raise ParsingError(f"Couldn't parse image height/width")


def get_relative_altitude(image_path, alt_source="default"):
    try:
        return parser_factory(image_path).get_relative_altitude(alt_source)
    except KeyError:
        raise ParsingError(f"Couldn't parse relative altitude")


def get_gsd(image_path, use_calibrated=False, corrected_alt=None, alt_source="default"):
    focal, pitch = get_camera_params(image_path, use_calibrated)
    if corrected_alt:
        alt = corrected_alt
    else:
        alt = get_relative_altitude(image_path, alt_source)

    gsd = pitch * alt / focal
    if gsd <= 0:
        raise ValueError("Parsed gsd is less than or equal to 0")

    return gsd
