"""
This package contains functions to extract imagery metadata from their exif and xmp tags.

Supports some DJI, some Hasselblad, some Sony, and all Sentera sensors.

Run ``imgparse --help`` on the command line to see all available CLI commands that are installed with the package.
"""

from imgparse._version import __version__
from imgparse.exceptions import ParsingError
from imgparse.getters import get_exif_data, get_xmp_data
from imgparse.imgparse import (  # get_bandnames,; get_wavelength_data,; get_ils,
    get_altitude_msl,
    get_autoexposure,
    get_camera_params,
    get_dimensions,
    get_firmware_version,
    get_focal_length,
    get_gsd,
    get_ils,
    get_lat_lon,
    get_make_and_model,
    get_pixel_pitch,
    get_relative_altitude,
    get_roll_pitch_yaw,
    get_timestamp,
    parse_session_alt,
)
from imgparse.metadata import get_metadata

__all__ = [
    "__version__",
    "get_xmp_data",
    "get_exif_data",
    "get_camera_params",
    "get_relative_altitude",
    "get_lat_lon",
    "get_altitude_msl",
    "get_roll_pitch_yaw",
    "get_focal_length",
    "get_make_and_model",
    "get_dimensions",
    "get_pixel_pitch",
    "parse_session_alt",
    "get_gsd",
    "get_timestamp",
    "get_autoexposure",
    "get_firmware_version",
    "get_metadata",
    "ParsingError",
    # "get_wavelength_data",
    # "get_bandnames",
    "get_ils",
]
