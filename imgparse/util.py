"""Utility functions for parsing metadata."""

import logging
import re
from io import BytesIO
from pathlib import Path
from typing import Any, Callable

import exifread
import xmltodict
from exifread.classes import IfdTag

from imgparse.exceptions import ParsingError
from imgparse.s3 import S3Path, s3_resource

logger = logging.getLogger(__name__)

# Exif and xmp are almost always located in the first 64KB
CHUNK_SIZE = 65536

# Define patterns:
FULL_XMP = re.compile(r"<x:xmpmeta.*</x:xmpmeta>", re.DOTALL)
XMP_END = re.compile(r"</x:xmpmeta>")


def get_exif_data(
    image_path: Path | S3Path, s3_role: str | None = None, current_data: bytes = b""
) -> tuple[dict[str, Any], bytes]:
    """
    Get a dictionary of lookup keys/values for the exif data of the provided image.

    This dictionary is an optional argument for the various ``imgparse`` functions to speed up processing by only
    reading the exif data once per image. Otherwise, this function is used internally for ``imgparse`` functions to
    extract the needed exif data.
    """
    start_byte = 0
    while True:
        current_data = read_raw_data(
            image_path,
            s3_role,
            read_size=start_byte + CHUNK_SIZE,
            current_data=current_data,
        )
        exif_data: dict[str, Any] = exifread.process_file(
            BytesIO(current_data), details=False
        )

        if exif_data:
            return exif_data, current_data

        start_byte = len(current_data)


def get_xmp_data(
    image_path: Path | S3Path, s3_role: str | None = None, current_data: bytes = b""
) -> tuple[dict[str, Any], bytes]:
    """Extract the xmp data of the provided image as a continuous string."""
    start_byte = 0
    while True:
        current_data = read_raw_data(
            image_path, s3_role, start_byte + CHUNK_SIZE, current_data
        )
        file_so_far = current_data.decode("latin_1")
        end_match = re.search(XMP_END, file_so_far)
        if end_match:
            match = re.search(FULL_XMP, file_so_far[:end_match.end()])
            if match:
                xmp_str = match.group(0)
                break
        start_byte = len(current_data)

    xmp_dict: dict[str, Any] = xmltodict.parse(xmp_str)

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
    return xmp_dict, current_data


def read_raw_data(
    image_path: Path | S3Path,
    s3_role: str | None = None,
    read_size: int = CHUNK_SIZE,
    current_data: bytes = b"",
) -> bytes:
    """
    Read raw bytes from image path.

    Takes `current_data` for external caching of data that is already read.
    """
    if len(current_data) < read_size:
        if isinstance(image_path, S3Path):
            obj = s3_resource(s3_role).Object(image_path.bucket, image_path.key)
            additional_data = obj.get(Range=f"bytes={len(current_data)}-{read_size}")[
                "Body"
            ].read()
        else:
            with open(image_path, "rb") as file:
                file.seek(len(current_data))
                additional_data = file.read(read_size - len(current_data))

        if not additional_data:
            raise ParsingError("Couldn't parse metadata. Reached the end of the file")

        return current_data + additional_data

    return current_data


def convert_to_degrees(tag: IfdTag) -> float:
    """Convert the `exifread` GPS coordinate IfdTag object to degrees in float format."""
    degrees = convert_to_float(tag, 0)
    minutes = convert_to_float(tag, 1)
    seconds = convert_to_float(tag, 2)

    return degrees + (minutes / 60.0) + (seconds / 3600.0)


def convert_to_float(tag: IfdTag, index: int = 0) -> float:
    """Convert `exifread` IfdTag object to float."""
    return float(tag.values[index].num) / float(tag.values[index].den)


def parse_seq(
    tag: dict[str, dict[str, list[str] | str]],
    type_cast_func: Callable[[str], Any] | None = None,
) -> list[Any]:
    """Parse an XML sequence."""
    seq = tag["rdf:Seq"]["rdf:li"]
    if not isinstance(seq, list):
        seq = [seq]
    if type_cast_func is not None:
        seq = [type_cast_func(item) for item in seq]

    return seq
