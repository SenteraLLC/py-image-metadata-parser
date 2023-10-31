"""Getter functions for various image data."""

import logging
import re
from io import BytesIO

import exifread
import xmltodict

from imgparse.decorators import memoize
from imgparse.exceptions import ParsingError

try:
    import boto3
except ImportError:
    boto3 = None

logger = logging.getLogger(__name__)

# Define misc constants:
CHUNK_SIZE = 10000

# Define patterns:
FULL_XMP = re.compile(r"<x:xmpmeta.*</x:xmpmeta>", re.DOTALL)
XMP_END = re.compile(r"</x:xmpmeta>")


@memoize
def get_xmp_data(image_path):
    """
    Extract the xmp data of the provided image as a continuous string.

    :param image_path: full path to image to parse xmp from
    :return: **xmp_data** - XMP data of image, as a string dump of the original XML
    :raises: ParsingError, FileNotFoundError
    """
    if image_path[:4] == "s3://":
        raise ValueError("File needs to be local to read xmp data")

    with open(image_path, encoding="latin_1") as file:
        xmp_dict = xmltodict.parse(_find_xmp_string(file))

    try:
        xmp_dict = xmp_dict["x:xmpmeta"]["rdf:RDF"]["rdf:Description"]
    except KeyError:
        logger.error("Couldn't parse xmp data for image: %s", image_path)
        raise ParsingError("Couldn't parse xmp data for image")

    # If there are too many xmp tags, returned as list
    if isinstance(xmp_dict, list):
        temp_dict = {}
        for d in xmp_dict:
            temp_dict.update(d)
        xmp_dict = temp_dict

    # Remove '@' signs, which appear to be non-consistent
    xmp_dict = {k.lstrip("@"): v for k, v in xmp_dict.items()}
    return xmp_dict


def read_exif_header_from_s3(image_path):
    """Read exif header from s3."""
    if boto3 is None:
        raise ImportError("boto3 needs to be installed to read exif from s3")

    bucket, key = image_path[5:].split("/", 1)
    obj = boto3.resource("s3").Object(bucket, key)

    # Read the entire exif header for the image and return it to be parsed by exifread
    return BytesIO(obj.get(Range="bytes=0-65536")["Body"].read())


@memoize
def get_exif_data(image_path):
    """
    Get a dictionary of lookup keys/values for the exif data of the provided image.

    This dictionary is an optional argument for the various ``imgparse`` functions to speed up processing by only
    reading the exif data once per image.  Otherwise this function is used internally for ``imgparse`` functions to
    extract the needed exif data.

    :param image_path: full path to image to parse exif from
    :return: **exif_data** - a dictionary of lookup keys/values for image exif data.
    :raises: ValueError, FileNotFoundError
    """
    if image_path[:5] == "s3://":
        file = read_exif_header_from_s3(image_path)
    else:
        file = open(image_path, "rb")

    exif_data = exifread.process_file(file, details=False)
    file.close()

    if not exif_data:
        logger.error("Couldn't read exif data for image: %s", image_path)
        raise ValueError("Couldn't read exif data for image")

    return exif_data


def _find_xmp_string(file):
    """
    Load chunks of an input image iteratively and search for the XMP data.

    On each iteration, a new chunk of the file (of size specified by xmp.CHUNK_SIZE) is read and
    appended to the already read portion of the file. The XMP regex is then matched against this string,
    and if the XMP data is found, returns the match. If no match is found, the function continues.

    :param file: Handler to file open for reading
    :return: **xmp_data**: XMP data of image, as string dump
    """
    file_so_far = ""
    while True:
        chunk = file.read(CHUNK_SIZE)

        # If at end of file, chunk will be None
        if not chunk:
            logger.error(
                "Couldn't parse XMP string from the image file. The image may not have XMP information"
            )
            raise ParsingError("Couldn't parse XMP string from the image file")

        start_search_at = max(
            0, len(file_so_far) - 12
        )  # 12 is the length of the ending XMP tag
        file_so_far += chunk

        end_match = re.search(XMP_END, file_so_far[start_search_at:])
        # If we matched the end, we know `file_so_far` contains the whole XMP string
        if end_match:
            return re.search(FULL_XMP, file_so_far).group(0)
