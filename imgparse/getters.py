"""Getter functions for various image data."""

import logging
import os

import exifread

import imgparse.xmp as xmp

logger = logging.getLogger(__name__)


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
        with open(image_path, encoding="mbcs") as file:
            img_str = file.read(xmp.MAX_FILE_READ_LENGTH)

        return xmp.find_first(img_str, xmp.FULL_XMP)

    except FileNotFoundError:
        logger.error("Couldn't read xmp data for image: %s", image_path)
        raise ValueError("Couldn't read xmp data from image.")


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