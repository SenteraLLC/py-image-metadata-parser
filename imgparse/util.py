"""Utility functions for parsing metadata."""

import logging
import re
from io import BytesIO
from pathlib import Path
from typing import Any, BinaryIO, Callable, Generator

import exifread
import xmltodict
from exifread.classes import IfdTag

from imgparse.exceptions import ParsingError
from imgparse.s3 import S3Path, s3_resource

logger = logging.getLogger(__name__)

# Define misc constants:
CHUNK_SIZE = 10000

# Define patterns:
FULL_XMP = re.compile(r"<x:xmpmeta.*</x:xmpmeta>", re.DOTALL)
XMP_END = re.compile(r"</x:xmpmeta>")


def get_exif_data(
    image_path: Path | S3Path, s3_role: str | None = None
) -> dict[str, Any]:
    """
    Get a dictionary of lookup keys/values for the exif data of the provided image.

    This dictionary is an optional argument for the various ``imgparse`` functions to speed up processing by only
    reading the exif data once per image. Otherwise, this function is used internally for ``imgparse`` functions to
    extract the needed exif data.
    """
    file: BinaryIO
    if isinstance(image_path, S3Path):
        obj = s3_resource(s3_role).Object(image_path.bucket, image_path.key)
        file = BytesIO(obj.get(Range="bytes=0-65536")["Body"].read())
    else:
        file = open(image_path, "rb")  # Open local file in binary mode

    exif_data: dict[str, Any] = exifread.process_file(file, details=False)
    file.close()

    if not exif_data:
        logger.error("Couldn't read exif data for image: %s", image_path)
        raise ValueError("Couldn't read exif data for image")

    return exif_data


def get_xmp_data(
    image_path: Path | S3Path, s3_role: str | None = None
) -> dict[str, Any]:
    """Extract the xmp data of the provided image as a continuous string."""
    xmp_dict: dict[str, Any] = xmltodict.parse(_read_xmp_string(image_path, s3_role))

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


def _xmp_chunk_generator_local(file_path: Path | str) -> Generator[str, None, None]:
    """Read chunks from a local file to look for xmp string."""
    with open(file_path, encoding="latin_1") as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            yield chunk


def _xmp_chunk_generator_s3(
    image_path: S3Path, s3_role: str | None = None
) -> Generator[str, None, None]:
    """Read chunks from an S3 file to look for xmp string."""
    s3_object = s3_resource(s3_role).Object(image_path.bucket, image_path.key)

    start_byte = 0
    while True:
        chunk = (
            s3_object.get(Range=f"bytes={start_byte}-{start_byte + CHUNK_SIZE - 1}")[
                "Body"
            ]
            .read()
            .decode("latin_1")
        )
        if not chunk:
            break
        yield chunk
        start_byte += CHUNK_SIZE


def _read_xmp_string(
    image_path: S3Path | Path | str, s3_role: str | None = None
) -> str:
    """Process chunks to search for the XMP block."""
    if isinstance(image_path, S3Path):
        chunk_generator = _xmp_chunk_generator_s3(image_path, s3_role)
    else:
        chunk_generator = _xmp_chunk_generator_local(image_path)

    file_so_far = ""
    for chunk in chunk_generator:
        start_search_at = max(
            0, len(file_so_far) - 12
        )  # Search for XMP_END within the last chunk
        file_so_far += chunk

        end_match = re.search(XMP_END, file_so_far[start_search_at:])
        if end_match:
            match = re.search(FULL_XMP, file_so_far)
            if match:
                return match.group(0)

    raise ParsingError("Couldn't parse XMP string from the image file")


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
