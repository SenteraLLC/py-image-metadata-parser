"""
This package contains functions to extract imagery metadata from their exif and xmp tags.

Supports some DJI, some Hasselblad, some Sony, and all Sentera sensors.

Run ``imgparse --help`` on the command line to see all available CLI commands that are installed with the package.
"""

from imgparse._version import __version__
from imgparse.altitude import AltitudeSource
from imgparse.exceptions import ParsingError, TerrainAPIError
from imgparse.parser import MetadataParser

__all__ = [
    "__version__",
    "ParsingError",
    "TerrainAPIError",
    "MetadataParser",
    "AltitudeSource",
]
