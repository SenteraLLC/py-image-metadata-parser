"""Getter functions for various image data."""

import logging
import re
from io import BytesIO
from pathlib import Path
from typing import Any, BinaryIO

import exifread
import xmltodict
from s3path import S3Path

from imgparse.exceptions import ParsingError
from imgparse.util import s3_resource

logger = logging.getLogger(__name__)

# Define misc constants:
CHUNK_SIZE = 10000

# Define patterns:
FULL_XMP = re.compile(r"<x:xmpmeta.*</x:xmpmeta>", re.DOTALL)
XMP_END = re.compile(r"</x:xmpmeta>")


def get_xmp_data(
    image_path: Path | S3Path, s3_role: str | None = None
) -> dict[str, Any]:
    """
    Extract the xmp data of the provided image as a continuous string.

    :param image_path: full path to image to parse xmp from
    :return: **xmp_data** - XMP data of image, as a string dump of the original XML
    """
    if isinstance(image_path, S3Path):
        xmp_string = read_xmp_string_s3(image_path, s3_role)
    else:
        xmp_string = read_xmp_string_local(image_path)

    xmp_dict: dict[str, Any] = xmltodict.parse(xmp_string)

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


def read_exif_header_from_s3(image_path: S3Path, s3_role: str | None = None) -> BytesIO:
    """Read exif header from s3."""
    obj = s3_resource(s3_role).Object(image_path.bucket, image_path.key)

    # Read the entire exif header for the image and return it as a BytesIO object
    return BytesIO(obj.get(Range="bytes=0-65536")["Body"].read())


def get_exif_data(
    image_path: Path | S3Path, s3_role: str | None = None
) -> dict[str, Any]:
    """
    Get a dictionary of lookup keys/values for the exif data of the provided image.

    This dictionary is an optional argument for the various ``imgparse`` functions to speed up processing by only
    reading the exif data once per image. Otherwise, this function is used internally for ``imgparse`` functions to
    extract the needed exif data.

    :param image_path: full path to image to parse exif from
    :return: **exif_data** - a dictionary of lookup keys/values for image exif data.
    """
    file: BinaryIO
    if isinstance(image_path, S3Path):
        file = read_exif_header_from_s3(image_path, s3_role)
    else:
        file = open(image_path, "rb")  # Open local file in binary mode

    exif_data: dict[str, Any] = exifread.process_file(file, details=False)
    file.close()

    if not exif_data:
        logger.error("Couldn't read exif data for image: %s", image_path)
        raise ValueError("Couldn't read exif data for image")

    return exif_data


def read_xmp_string_local(image_path: Path | str) -> str:
    """
    Load chunks of an input image iteratively and search for the XMP data.

    On each iteration, a new chunk of the file (of size specified by CHUNK_SIZE) is read and
    appended to the already read portion of the file. The XMP regex is then matched against this string,
    and if the XMP data is found, returns the match. If no match is found, the function continues.

    :param file: Handler to file open for reading in binary mode
    :return: **xmp_data**: XMP data of image, as a string dump
    """
    file_so_far = ""

    with open(image_path, encoding="latin_1") as f:
        while True:
            chunk = f.read(CHUNK_SIZE)

            if not chunk:
                raise ParsingError("Couldn't parse XMP string from the image file")

            start_search_at = max(
                0, len(file_so_far) - 12
            )  # 12 is the length of the ending XMP tag
            file_so_far += chunk

            end_match = re.search(XMP_END, file_so_far[start_search_at:])
            # If we matched the end, we know `file_so_far` contains the whole XMP string
            if end_match:
                match = re.search(FULL_XMP, file_so_far)
                return match.group(0) if match else ""


def read_xmp_string_s3(image_path: S3Path, s3_role: str | None = None) -> str:
    """Read XMP data from an image stored in S3 by reading chunks and searching for the XMP block."""
    obj = s3_resource(s3_role).Object(image_path.bucket, image_path.key)
    file_so_far = ""
    start_byte = 0

    while True:
        # Get the next chunk of data from S3
        chunk = (
            obj.get(Range=f"bytes={start_byte}-{start_byte + CHUNK_SIZE - 1}")["Body"]
            .read()
            .decode("latin_1")
        )
        if not chunk:
            raise ParsingError("Couldn't parse XMP string from the image file")

        file_so_far += chunk
        start_search_at = max(
            0, len(file_so_far) - 12
        )  # Search for XMP_END within the last chunk

        end_match = re.search(XMP_END, file_so_far[start_search_at:])
        if end_match:
            match = re.search(FULL_XMP, file_so_far)
            return match.group(0) if match else ""

        # Move the start byte to the next chunk
        start_byte += CHUNK_SIZE
