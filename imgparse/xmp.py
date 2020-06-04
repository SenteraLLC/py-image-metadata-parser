"""Extract XMP data from images."""

import io
import logging
import re
from functools import reduce
from typing import List, NamedTuple

logger = logging.getLogger(__name__)

# Define misc constants:
CHUNK_SIZE = 10000

# Define patterns:
FULL_XMP = re.compile(r"<x:xmpmeta.*</x:xmpmeta>", re.DOTALL)
XMP_END = re.compile(r"</x:xmpmeta>")
SEQ = re.compile(r"(?: *|\t)<rdf:li>(.*)</rdf:li>\n")

# Sentera-exclusive patterns:
ILS = re.compile(r"<Camera:SunSensor>.*</Camera:SunSensor>", re.DOTALL)


class XMPTagNotFoundError(Exception):
    """Custom exception for when a match on a specific XMP tag fails."""

    pass


class SensorMake(NamedTuple):
    """
    Named tuple storing the regex patterns to match against for various XMP values of different sensors.

    For example, Sentera sensors preface most XMP data with the "Camera:" prefix, while DJI sensors use "drone-dji".
    Instances of this named tuple for each of these makes are below.
    """

    RELATIVE_ALT: re.Pattern
    ROLL: re.Pattern
    PITCH: re.Pattern
    YAW: re.Pattern


Sentera = SensorMake(
    RELATIVE_ALT=re.compile(r'Camera:AboveGroundAltitude="([0-9]+.[0-9]+)"'),
    ROLL=re.compile(r'Camera:Roll="(-?[0-9]+.[0-9]+)"'),
    PITCH=re.compile(r'Camera:Pitch="(-?[0-9]+.[0-9]+)"'),
    YAW=re.compile(r'Camera:Yaw="(-?[0-9]+.[0-9]+)"'),
)

DJI = SensorMake(
    RELATIVE_ALT=re.compile(r'drone-dji:RelativeAltitude="(-?\+?[0-9]+.[0-9]+)"'),
    ROLL=re.compile(r'drone-dji:GimbalRollDegree="(-?\+?[0-9]+.[0-9]+)"'),
    PITCH=re.compile(r'drone-dji:GimbalPitchDegree="(-?\+?[0-9]+.[0-9]+)"'),
    YAW=re.compile(r'drone-dji:GimbalYawDegree="(-?\+?[0-9]+.[0-9]+)"'),
)


def find_xmp_string(file: io.TextIOWrapper):
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
                "Couldn't parse XMP string from the image file. The image may not have XMP information."
            )
            raise XMPTagNotFoundError("Couldn't parse XMP string from the image file.")

        start_search_at = max(
            0, len(file_so_far) - 12
        )  # 12 is the length of the ending XMP tag
        file_so_far += chunk

        end_match = re.search(XMP_END, file_so_far[start_search_at:])
        # If we matched the end, we know `file_so_far` contains the whole XMP string
        if end_match:
            return re.search(FULL_XMP, file_so_far).group(0)


def find(xmp_data: str, patterns: List[re.Pattern]) -> str:
    """
    Sequentially apply a list of patterns to the xmp data to parse a value of interest.

    This function recurses over the list of patterns, applying each one to the remaining matching XMP string
    and passing the subsequent matching string to the next iteration.

    If multiple capture groups are in a passed pattern, that pattern must be the last pattern in the list --
    in this situation, a tuple will be returned with each matched group. This can be useful when matching tags
    in a "<rdf:Seq>".

    :param xmp_data: XMP string to be parsed
    :param patterns: List of patterns to be applied to the XMP string
    :return: **match** -- Matched string (if all matches are successful)
    :raises: XMPTagNotFoundError
    """

    def _find_inner(partial_xmp: str, pattern: re.Pattern) -> str:
        match = pattern.findall(partial_xmp)

        # If called on a string but no match was found, findall() returns an empty list:
        if match:
            # Returns the whole match
            return match[0]
        else:
            raise XMPTagNotFoundError(
                "A tag pattern did not match with the XMP string. The tag may not exist."
            )

    return reduce(_find_inner, patterns, xmp_data)
