"""Return types that include multiple values."""

from enum import Enum
from typing import NamedTuple


class Quaternion(NamedTuple):
    """Quaternion rotation."""

    q0: float
    q1: float
    q2: float
    q3: float


class Euler(NamedTuple):
    """Euler rotation."""

    roll: float
    pitch: float
    yaw: float


class WorldCoords(NamedTuple):
    """World coordinates."""

    lat: float
    lon: float


class PixelCoords(NamedTuple):
    """Pixel coordinates."""

    x: float
    y: float


class Dimensions(NamedTuple):
    """Image dimensions."""

    height: int
    width: int


class Version(NamedTuple):
    """Firmware version."""

    major: int
    minor: int
    patch: int


class DistortionParams(NamedTuple):
    """Distortion parameters in OpenCV order."""

    k1: float
    k2: float
    p1: float
    p2: float
    k3: float


class AltitudeSource(Enum):
    """Altitude source enum."""

    default = "default"
    terrain = "terrain"
    lrf = "lrf"
