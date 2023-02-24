from imgparse import xmp
from imgparse.decorators import get_if_needed
from imgparse.getters import get_exif_data, get_xmp_data
from imgparse.exceptions import ParsingError
from imgparse.util import parse_seq, convert_to_float

from .parser import get_make_and_model


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
        central_wavelength = parse_seq(xmp_data[xmp_tags.WAVELENGTH_CENTRAL], int)
        wavelength_fwhm = parse_seq(xmp_data[xmp_tags.WAVELENGTH_FWHM], int)
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
        return parse_seq(xmp_data[xmp_tags.BANDNAME])
    except KeyError:
        raise ParsingError("Couldn't parse bandnames. Sensor might not be supported")