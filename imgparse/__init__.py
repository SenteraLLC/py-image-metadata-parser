"""
This package contains functions to extract imagery metadata from their exif and xmp tags.

Supports some DJI, some Hasselblad, some Sony, and all Sentera sensors.

All functions take an image path as an argument for easy use, but optionally can take the dictionary of exif and/or xmp
key/value pairs returned by ``imgparse.get_exif_data()`` and ``imgparse.get_xmp_data()``.  This allows the user to
avoid rereading the exif/xmp data for an image when extracting multiple kinds of metadata in order to speed up
processing.  Example code for using this functionality is shown below.

.. code-block:: python

    exif_data = imgparse.get_exif_data(image_path)
    xmp_data = imgparse.get_xmp_data(image_path)
    make, model = imgparse.get_make_and_model(exif_data=exif_data)
    lat, lon = imgparse.get_lat_lon(exif_data=exif_data)
    focal_length, pixel_pitch = imgparse.get_camera_params(exif_data=exif_data)
    roll, pitch, yaw = imgparse.get_roll_pitch_yaw(exif_data=exif_data, xmp_data=xmp_data)

"""

from imgparse._version import __version__
from imgparse.getters import get_exif_data, get_xmp_data
from imgparse.imgparse import (
    get_altitude_msl,
    get_autoexposure,
    get_camera_params,
    get_dimensions,
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
    "get_ils",
    "get_timestamp",
    "get_autoexposure",
]
