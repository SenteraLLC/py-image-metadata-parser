"""
This package contains functions to extract imagery metadata from their exif and xmp tags.

Supports some DJI, some Hasselblad, some Sony, and all Sentera sensors.

Run ``imgparse --help`` on the command line to see all available CLI commands that are installed with the package.
"""

from imgparse._version import __version__
from imgparse.exceptions import ParsingError, TerrainAPIError
from imgparse.getters import get_exif_data, get_xmp_data
from imgparse.imgparse import (
    get_altitude_msl,
    get_autoexposure,
    get_bandnames,
    get_camera_params,
    get_dimensions,
    get_distortion_parameters,
    get_firmware_version,
    get_focal_length,
    get_focal_length_pixels,
    get_gsd,
    get_home_point,
    get_ils,
    get_lat_lon,
    get_lens_model,
    get_make_and_model,
    get_pixel_pitch,
    get_principal_point,
    get_relative_altitude,
    get_roll_pitch_yaw,
    get_serial_number,
    get_timestamp,
    get_unique_id,
    get_wavelength_data,
    parse_session_alt,
    get_irradiance,
)
from imgparse.metadata import get_metadata

__all__ = [
    "__version__",
    "get_xmp_data",
    "get_exif_data",
    "get_camera_params",
    "get_distortion_parameters",
    "get_relative_altitude",
    "get_lat_lon",
    "get_altitude_msl",
    "get_roll_pitch_yaw",
    "get_focal_length",
    "get_focal_length_pixels",
    "get_principal_point",
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
    "get_wavelength_data",
    "get_bandnames",
    "get_ils",
    "get_home_point",
    "get_serial_number",
    "TerrainAPIError",
    "get_lens_model",
    "get_unique_id",
    "get_irradiance",
]
