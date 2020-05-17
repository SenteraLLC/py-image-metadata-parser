"""Extract XMP data from images."""

import re
from functools import reduce
from typing import List, NamedTuple, Optional

# Define misc constants:
MAX_FILE_READ_LENGTH = 25000

# Define patterns:
FULL_XMP = re.compile(r"<x:xmpmeta.*</x:xmpmeta>", re.DOTALL)
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


def find_first(xmp_data: str, pattern: re.Pattern) -> Optional[str]:
    """
    Apply a single pattern to the xmp data, and return the first match.

    This function has an advantage over the more general "find" function
    in very limited circumstances. It is faster, is only useful if you
    want to match on only one pattern, return the whole match (no ignored
    capture groups), and only want the first match found.

    :param xmp_data: XMP string to be parsed
    :param pattern: pattern to be applied to the XMP string
    :return: **match** -- matched string (if match is successful), or None if the match fails
    """
    return pattern.search(xmp_data).group(0)


def find(xmp_data: str, patterns: List[re.Pattern]) -> Optional[str]:
    """
    Sequentially apply a list of patterns to the xmp data to parse a value of interest.

    This function recurses over the list of patterns, applying each one to the remaining matching XMP string
    and passing the subsequent matching string to the next iteration.

    Instead of raising an exception if a match fails, this function explicitly returns None so that functions
    that wrap this function to parse specific values can handle errors themselves and output more helpful messages.
    This is denoted by the Optional[str] return type, but unfortunately returning this type does not enforce a
    None-check on the part of the caller.

    :param xmp_data: XMP string to be parsed
    :param patterns: List of patterns to be applied to the XMP string
    :return: **match** -- Matched string (if all matches are successful), or None if a match fails
    """

    def _find_inner(partial_xmp: str, pattern: re.Pattern) -> str:
        match = pattern.findall(partial_xmp)

        # If called on a string but no match was found, findall() returns an empty list:
        if match:
            # Returns the whole match
            return match[0]
        else:
            raise XMPTagNotFoundError(
                f"A tag pattern did not match with the XMP string. The tag "
                f"may not exist, or the pattern may be invalid."
            )

    return reduce(_find_inner, patterns, xmp_data)
