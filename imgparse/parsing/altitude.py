import logging
import os

import requests

from imgparse import xmp
from imgparse.decorators import get_if_needed, memoize
from imgparse.exceptions import ParsingError, TerrainAPIError
from imgparse.getters import get_exif_data, get_xmp_data
from imgparse.util import convert_to_float

from .parser import get_make_and_model, get_lat_lon, get_focal_length

logger = logging.getLogger(__name__)

TERRAIN_URL = "https://maps.googleapis.com/maps/api/elevation/json"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

def _parse_session_alt(image_path):
    """
    Get the session ground altitude (meters above msl) from a `session.txt` file.

    Used for Sentera cameras since relative altitude isn't stored in exif or xmp tags, and instead the session ground
    altitude is written as a text file that needs to be read.  The `session.txt` must be in the same directory as the
    image in order to be read.

    :param image_path: the full path to the image
    :return: **ground_alt** - the session ground altitude, used to calculate relative altitude.
    :raises: ParsingError
    """
    imagery_dir = os.path.dirname(image_path)
    session_path = os.path.join(imagery_dir, "session.txt")
    if not os.path.isfile(session_path):
        raise ParsingError("Couldn't find session.txt file in image directory")

    session_file = open(session_path, "r")
    session_alt = session_file.readline().split("\n")[0].split("=")[1]
    session_file.close()
    if not session_alt:
        raise ParsingError("Couldn't parse session altitude from session.txt")

    return float(session_alt)


def _compute_terrain_offset(image_path, exif_data, xmp_data, api_key):
    """
    Get relative terrain elevation for the image from google's terrain api.

    Relative terrain elevation is the flight home point terrain elevation - the image terrain elevation.
    The relative altitude stored in an image's xmp data is relative to the home point takeoff, not the
    altitude of the drone above the ground at each image location. We add the relative terrain elevation
    to the relative altitude to get the actual altitude of the drone above the ground.
    """
    if api_key is None:
        api_key = GOOGLE_API_KEY

    home_lat, home_lon = _get_home_point(image_path, exif_data, xmp_data)
    image_lat, image_lon = get_lat_lon(image_path, exif_data)
    home_elevation = _get_home_point_elevation(home_lat, home_lon, api_key)
    image_elevation = _get_terrain_elevation(image_lat, image_lon, api_key)
    return home_elevation - image_elevation


def _get_terrain_elevation(lat, lon, api_key):
    """Call out to the google elevation api to get the terrain elevation at a given lat/lon."""
    params = {
        "locations": f"{lat} {lon}",
        "key": api_key,
    }
    response = requests.request("GET", TERRAIN_URL, params=params).json()
    if response["status"] != "OK":
        logger.warning("Couldn't access google terrain api")
        raise TerrainAPIError("Couldn't access google terrain api")
    return response["results"][0]["elevation"]


@memoize
def _get_home_point_elevation(lat, lon, api_key):
    """
    Memoized wrapper around `get_terrain_elevation()`.

    Ensure we aren't making multiple calls to google to get the same home point elevation for images from the
    same flight.
    """
    return _get_terrain_elevation(lat, lon, api_key)


def _get_home_point(image_path, exif_data, xmp_data):
    """
    Get the flight home point. Used for `get_altitude_agl(alt_source=terrain)`.

    :param image_path: the full path to the image
    :param exif_data: used internally for memoization. Not necessary to supply.
    :param xmp_data: used internally for memoization. Not necessary to supply.
    :return: **lat**, **lon** - coordinates of flight home point
    """
    try:
        make, model = get_make_and_model(image_path, exif_data)
        xmp_tags = xmp.get_tags(make)
        if make == "DJI":
            self_data = xmp_data[xmp_tags.SELF_DATA].split("|")
            if len(self_data) == 4:
                return float(self_data[0]), float(self_data[1])
            else:
                raise KeyError()
        elif make == "Sentera":
            return float(xmp_data[xmp_tags.HOMEPOINT_LAT]), float(
                xmp_data[xmp_tags.HOMEPOINT_LON]
            )
        else:
            raise KeyError()
    except KeyError:
        logger.warning(
            "Couldn't parse home point. Sensor might not be supported for terrain elevation parsing"
        )
        raise ParsingError(
            "Couldn't parse home point. Sensor might not be supported for terrain elevation parsing"
        )


@get_if_needed("exif_data", getter=get_exif_data, getter_args=["image_path"])
@get_if_needed("xmp_data", getter=get_xmp_data, getter_args=["image_path"])
def get_altitude_agl(
    image_path,
    exif_data=None,
    xmp_data=None,
    alt_source="default",
    terrain_api_key=None,
    fallback=True,
):
    """
    Get the relative altitude of the sensor above the ground (in meters) when the image was taken.

    `alt_source` by default will grab the relative altitude stored in the image's xmp data. Other options are `lrf` to
    use the altitude detected from a laser range finder or `terrain` to use google's terrain api to correct the relative
    altitude with the terrain elevation change from the home point. If a non-default `alt_source` is specified and
    fails, the function will "fallback" and return the default xmp relative altitude instead. To disable this fallback
    and raise an error if the specified `alt_source` isn't available, set `fallback` to False.

    There is an additional fallback if the image is from an older firmware Sentera sensor. For older Sentera sensor's,
    this xmp tag will not exist, and instead the relative altitude must be computed using the `session.txt` file
    associated with the image instead.

    :param image_path: the full path to the image
    :param exif_data: used internally for memoization. Not necessary to supply.
    :param xmp_data: used internally for memoization. Not necessary to supply.
    :param alt_source: Set to "lrf" for laser range finder. "terrain" for terrain aware altitude.
    :param terrain_api_key: Required if `alt_source` set to "terrain". API key to access google elevation api.
    :param fallback: If disabled and the specified `alt_source` fails, will throw an error instead of falling back.
    :return: **relative_alt** - the relative altitude of the camera above the ground
    :raises: ParsingError
    """
    make, model = get_make_and_model(image_path, exif_data)
    xmp_tags = xmp.get_tags(make)
    terrain_alt = 0
    if alt_source == "lrf":
        try:
            try:
                return float(xmp_data[xmp_tags.LRF_ALT])
            except KeyError:
                # Specific logic to handle quad v1.0.0 incorrect tag
                return float(xmp_data[xmp_tags.LRF_ALT2])
        except KeyError:
            logger.warning(
                "Altimeter calculated altitude not found in XMP. Defaulting to relative altitude"
            )
    elif alt_source == "terrain":
        try:
            terrain_alt = _compute_terrain_offset(
                image_path, exif_data, xmp_data, terrain_api_key
            )
            # We set alt source to default here if successfully parsed terrain altitude
            # to avoid incorrectly failing below if fallback is set to False
            alt_source = "default"
        except ParsingError:
            logger.warning(
                "Couldn't determine terrain elevation. Defaulting to relative altitude"
            )
        except TerrainAPIError:
            if not fallback:
                raise

    if alt_source != "default" and not fallback:
        raise ParsingError(
            f"Fallback disabled. Couldn't parse relative altitude for given alt_source: {alt_source}"
        )

    try:
        return float(xmp_data[xmp_tags.RELATIVE_ALT]) + terrain_alt
    except KeyError:
        if make == "Sentera":
            logger.warning(
                "Relative altitude not found in XMP. Attempting to parse from session.txt file"
            )
            abs_alt = get_altitude_msl(image_path)
            session_alt = _parse_session_alt(image_path)
            return abs_alt - session_alt
        else:
            raise ParsingError(
                "Couldn't parse relative altitude from xmp data. Sensor may not be supported"
            )


@get_if_needed("exif_data", getter=get_exif_data, getter_args=["image_path"])
def get_altitude_msl(image_path, exif_data=None):
    """
    Get the absolute altitude (meters above msl) of the sensor when the image was taken.

    :param image_path: the full path to the image
    :param exif_data: used internally for memoization. Not necessary to supply.
    :return: **altitude_msl** - the absolute altitude of the image in meters.
    :raises: ParsingError
    """
    try:
        return convert_to_float(exif_data["GPS GPSAltitude"])
    except KeyError:
        raise ParsingError("Couldn't parse altitude msl. Sensor might not be supported")


@get_if_needed("exif_data", getter=get_exif_data, getter_args=["image_path"])
@get_if_needed("xmp_data", getter=get_xmp_data, getter_args=["image_path"])
def get_gsd(
    image_path,
    exif_data=None,
    xmp_data=None,
    corrected_alt=None,
    calibrated_fl=False,
    alt_source="default",
    terrain_api_key=None,
    fallback=True,
):
    """
    Get the gsd of the image (in meters/pixel).

    :param image_path: the full path to the image
    :param exif_data: used internally for memoization. Not necessary to supply.
    :param xmp_data: used internally for memoization. Not necessary to supply.
    :param corrected_alt: corrected relative altitude (optional)
    :param calibrated_fl: enable to use calibrated focal length if available
    :param alt_source: See `get_relative_altitude()`
    :param terrain_api_key: Required if `alt_source` set to "terrain". API key to access google elevation api.
    :param fallback: Raise an error if the specified `alt_source` can't be accessed
    :return: **gsd** - the ground sample distance of the image in meters
    :raises: ParsingError
    """
    focal_length = get_focal_length(
        image_path, exif_data, xmp_data, calibrated_fl
    )
    if corrected_alt:
        alt = corrected_alt
    else:
        alt = get_altitude_agl(
            image_path,
            exif_data,
            xmp_data,
            alt_source,
            terrain_api_key=terrain_api_key,
            fallback=fallback,
        )

    gsd = alt / focal_length
    if gsd <= 0:
        raise ValueError("Parsed gsd is less than or equal to 0")

    return gsd
