"""Extract XMP data from images."""

import re
from functools import reduce
from typing import List, NamedTuple, Optional

# Define misc constants:
MAX_FILE_READ_LENGTH = 15000

# Define patterns:
FULL_XMP = re.compile(r"<x:xmpmeta.*</x:xmpmeta>", re.DOTALL)
SEQ = re.compile(r"(?: *|\t)<rdf:li>(.*)</rdf:li>\n")

# Sentera-exclusive patterns:
ILS = re.compile(r"<Camera:SunSensor>.*</Camera:SunSensor>", re.DOTALL)


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

    def _find_inner(partial_xmp: Optional[str], pattern: re.Pattern) -> Optional[str]:
        # The try block catches exceptions from trying to match on a None returned by a previous match:
        try:
            match = pattern.findall(partial_xmp)
            # If called on a string but no match was found, findall() returns an empty list:
            if match:
                # Returns the whole match
                return match[0]
            else:
                return None
        except TypeError:
            return None

    return reduce(_find_inner, patterns, xmp_data)
