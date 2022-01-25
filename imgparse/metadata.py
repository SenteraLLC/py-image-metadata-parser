"""Functions for generic metadata retrieval."""

from typing import Callable, NamedTuple

import imgparse


class Metadata(NamedTuple):
    """Struct-like type representing a type of metadata, and the method to retrieve it."""

    name: str
    method: Callable


AUTOEXPOSURE = Metadata(name="Autoexposure", method=imgparse.get_autoexposure)
TIMESTAMP = Metadata(name="Timestamp", method=imgparse.get_timestamp)
PIXEL_PITCH = Metadata(name="Pixel pitch (m)", method=imgparse.get_pixel_pitch)
FOCAL_LENGTH = Metadata(name="Focal length (m)", method=imgparse.get_focal_length)
CAMERA_PARAMS = Metadata(
    name="(Focal length (m), Pixel pitch (m))", method=imgparse.get_camera_params
)
RELATIVE_ALT = Metadata(name="Altitude (m)", method=imgparse.get_relative_altitude)
LAT_AND_LON = Metadata(name="(Lat, Lon)", method=imgparse.get_lat_lon)
ALTITUDE_MSL = Metadata(name="Altitude MSL (m)", method=imgparse.get_altitude_msl)
ROLL_PITCH_YAW = Metadata(
    name="(Roll (degrees), Pitch (degrees), Yaw (degrees))",
    method=imgparse.get_roll_pitch_yaw,
)
MAKE_AND_MODEL = Metadata(name="(Make, Model)", method=imgparse.get_make_and_model)
DIMENSIONS = Metadata(name="Dimensions", method=imgparse.get_dimensions)
GSD = Metadata(name="Gsd (m)", method=imgparse.get_gsd)
FIRMWARE = Metadata(name="Firmware version", method=imgparse.get_firmware_version)
# WAVELENGTH = Metadata(
#     name="Central Wavelength, WavelengthFWHM", method=imgparse.get_wavelength_data
# )
# BANDNAME = Metadata(name="BandName", method=imgparse.get_bandnames)
# ILS = Metadata(name="ILS", method=imgparse.get_ils)


def get_metadata(image_path: str, *metadata: Metadata):
    """
    Get a selection of supported metadata from the image.

    Simple wrapper function that calls the individual get_* functions that match the names of the metadata
    requested. This is useful when a user would like to get multiple metadata (e.g. GSD and lat/lon) in one
    function call, rather than listing each call individually. Metadata are specified via the provided
    `Metadata` instances -- this allows for IDE-assisted autocompletion and the prevention of misspelled
    or non-existent metadata types.

    :param image_path: the full path to the image
    :param metadata: variable number of Metadata arguments
    :return: **parsed_metadata** -- A tuple of values of all requested metadata
    """
    return (metadata_type.method(image_path) for metadata_type in metadata)
