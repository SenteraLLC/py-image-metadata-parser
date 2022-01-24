"""Getter functions for various image data."""

import logging
import os

import exifread
import xmltodict

import imgparse.xmp as xmp
from imgparse.decorators import memoize

logger = logging.getLogger(__name__)


@memoize
def get_xmp_data(image_path):
    """
    Extract the xmp data of the provided image as a continuous string.

    :param image_path: full path to image to parse xmp from
    :return: **xmp_data** - XMP data of image, as a string dump of the original XML
    :raises: ValueError
    """
    if not image_path or not os.path.isfile(image_path):
        logger.error(
            "Image doesn't exist.  Couldn't read xmp data for image: %s", image_path
        )
        raise ValueError("Image doesn't exist. Couldn't read xmp data")

    try:
        with open(image_path, encoding="latin_1") as file:
            xmp_dict = xmltodict.parse(xmp.find_xmp_string(file))["x:xmpmeta"][
                "rdf:RDF"
            ]["rdf:Description"]
            if isinstance(xmp_dict, list):
                xmp_dict = xmp_dict[0]
            if isinstance(xmp_dict, dict):
                return xmp_dict
            else:
                raise ValueError("Couldn't parse xmp data")

    except FileNotFoundError:
        logger.error("Image file at path %s could not be found.", image_path)
        raise ValueError("Image file could not be found.")


@memoize
def get_exif_data(image_path):
    """
    Get a dictionary of lookup keys/values for the exif data of the provided image.

    This dictionary is an optional argument for the various ``imgparse`` functions to speed up processing by only
    reading the exif data once per image.  Otherwise this function is used internally for ``imgparse`` functions to
    extract the needed exif data.

    :param image_path: full path to image to parse exif from
    :return: **exif_data** - a dictionary of lookup keys/values for image exif data.
    :raises: ValueError
    """
    if not image_path or not os.path.isfile(image_path):
        logger.error(
            "Image doesn't exist.  Can't read exif data for image: %s", image_path
        )
        raise ValueError("Image doesn't exist. Couldn't read exif data.")

    file = open(image_path, "rb")
    exif_data = exifread.process_file(file, details=False)
    file.close()

    if not exif_data:
        logger.error("Couldn't read exif data for image: %s", image_path)
        raise ValueError("Couldn't read exif data for image.")

    return exif_data
