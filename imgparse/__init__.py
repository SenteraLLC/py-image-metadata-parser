"""
This module contains various functions that extract imagery information from exif and xmp tags in images.

Supports some DJI, some Hasselblad, one Sony, and all Sentera sensors.

All functions take an image path as an argument for easy use, but optionally can take the dictionary of exif key/value
pairs returned by ``imgparse.get_exif_data()``.  This allows the user to avoid rereading the exif data for an image
when extracting different kinds of metadata in order to speed up processing.  Example code for using this functionality
is shown below.

.. code-block:: python

    exif_data = imgparse.get_exif_data(image_path)
    make, model = imgparse.get_make_and_model(exif_data=exif_data)
    lat, lon = imgparse.get_lat_lon(exif_data=exif_data)
    focal_length, pixel_pitch = imgparse.get_camera_params(exif_data=exif_data)

"""

from imgparse._version import __version__
from imgparse.create_analytics_metadata import create_analytics_metadata
from imgparse.imgparse import (
    get_altitude_msl,
    get_camera_params,
    get_dimensions,
    get_exif_data,
    get_focal_length,
    get_gsd,
    get_lat_lon,
    get_make_and_model,
    get_relative_altitude,
    get_roll_pitch_yaw,
    get_sentera_pixel_pitch,
    get_xmp_data,
    parse_session_alt,
)

__all__ = [
    "__version__",
    "create_analytics_metadata",
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
    "get_sentera_pixel_pitch",
    "parse_session_alt",
    "get_gsd",
]
