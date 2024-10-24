"""Return types that include multiple values."""

from collections import namedtuple
from enum import Enum

Quaternion = namedtuple("Quaternion", "q0 q1 q2 q3")
Euler = namedtuple("Euler", "roll pitch yaw")
Coords = namedtuple("Coords", "lat lon")
PixelCoords = namedtuple("PixelCoords", "x y")
Dimensions = namedtuple("Dimensions", "height width")
Version = namedtuple("Version", "major minor patch")


class AltitudeSource(Enum):
    """Altitude source enum."""

    default = "default"
    terrain = "terrain"
    lrf = "lrf"
