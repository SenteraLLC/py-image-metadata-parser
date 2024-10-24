"""Functionality related to parsing altitude."""

import logging
import os
from functools import lru_cache
from pathlib import Path

import requests

from imgparse.exceptions import ParsingError, TerrainAPIError
from imgparse.s3 import S3Path

logger = logging.getLogger(__name__)

TERRAIN_URL = "https://maps.googleapis.com/maps/api/elevation/json"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


def parse_session_alt(image_path: Path | S3Path) -> float:
    """
    Get the session ground altitude (meters above msl) from a `session.txt` file.

    Used for Sentera cameras since relative altitude isn't stored in exif or xmp tags, and instead the session ground
    altitude is written as a text file that needs to be read.  The `session.txt` must be in the same directory as the
    image in order to be read.
    """
    if isinstance(image_path, S3Path):
        raise ParsingError("File needs to be local to parse session.txt")

    session_path = image_path.parent / "session.txt"
    if not session_path.is_file():
        raise ParsingError("Couldn't find session.txt file in image directory")

    with open(session_path, "r") as f:
        session_alt = f.readline().strip().split("=")[1]

    if not session_alt:
        raise ParsingError("Couldn't parse session altitude from session.txt")

    return float(session_alt)


@lru_cache(maxsize=None)
def hit_terrain_api(lat: float, lon: float, api_key: str | None = None) -> float:
    """Hit the google elevation api to get the terrain elevation at a given lat/lon."""
    if api_key is None:
        api_key = GOOGLE_API_KEY

    params = {
        "locations": f"{lat} {lon}",
        "key": api_key,
    }
    response = requests.request("GET", TERRAIN_URL, params=params).json()
    if response["status"] != "OK":
        logger.warning("Couldn't access google terrain api")
        raise TerrainAPIError("Couldn't access google terrain api")
    return float(response["results"][0]["elevation"])
