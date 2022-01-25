import os
import re
import logging
import pytz
from datetime import datetime
from timezonefinder import TimezoneFinder

from imgparse.exceptions import ParsingError
from imgparse.utils import convert_to_float, convert_to_degrees

logger = logging.getLogger(__name__)


class Parser:
    def __init__(self, exif_data, xmp_data, make, model, path):
        self.exif_data = exif_data
        self.xmp_data = xmp_data
        self.make = make
        self.model = model
        self.path = path

    def get_altitude_msl(self):
        return convert_to_float(self.exif_data["GPS GPSAltitude"])

    def get_autoexposure(self):
        iso = self.exif_data["EXIF ISOSpeedRatings"].values[0]
        integration_time = convert_to_float(self.exif_data["EXIF ExposureTime"])
        return iso * integration_time

    def get_focal_length(self, use_calibrated=False):
        if use_calibrated:
            logger.warning("Calibrated focal length unavailable. Defaulting to uncalibrated focal length")

        return convert_to_float(self.exif_data["EXIF FocalLength"]) / 1000

    def get_firmware_version(self):
        version_match = re.search(
            "[0-9]+.[0-9]+.[0-9]+", self.exif_data["Image Software"].values
        )
        if not version_match:
            raise ParsingError("Couldn't parse sensor version")
        major, minor, patch = version_match.group(0).split(".")
        return int(major), int(minor), int(patch)

    def get_timestamp(self, format_string="%Y:%m:%d %H:%M:%S"):
        try:
            datetime_obj = datetime.strptime(
                self.exif_data["EXIF DateTimeOriginal"].values, format_string
            )
        except ValueError:
            raise ParsingError("Couldn't parse found timestamp with given format string")

        lat, lon = self.get_lat_lon()
        timezone = pytz.timezone(TimezoneFinder().timezone_at(lng=lon, lat=lat))
        return timezone.localize(datetime_obj)

    def get_lat_lon(self):
        gps_latitude = self.exif_data["GPS GPSLatitude"]
        gps_latitude_ref = self.exif_data["GPS GPSLatitudeRef"]
        gps_longitude = self.exif_data["GPS GPSLongitude"]
        gps_longitude_ref = self.exif_data["GPS GPSLongitudeRef"]

        lat = convert_to_degrees(gps_latitude)
        if gps_latitude_ref.values[0] != "N":
            lat = 0 - lat

        lon = convert_to_degrees(gps_longitude)
        if gps_longitude_ref.values[0] != "E":
            lon = 0 - lon

        return lat, lon

    def get_dimensions(self):
        ext = os.path.splitext(self.path)[-1].lower()
        if ext in [".jpg", ".jpeg"]:
            return (
                self.exif_data["EXIF ExifImageLength"].values[0],
                self.exif_data["EXIF ExifImageWidth"].values[0],
            )
        elif ext in [".tif", ".tiff"]:
            return (
                self.exif_data["Image ImageLength"].values[0],
                self.exif_data["Image ImageWidth"].values[0],
            )
        else:
            raise ParsingError(f"Image type: {ext} isn't supported")

    def get_roll_pitch_yaw(self):
        raise ParsingError(f"Couldn't extract roll/pitch/yaw. Sensor type {self.make} isn't supported")

    def get_pixel_pitch(self):
        raise ParsingError(f"Couldn't extract pixel pitch. Sensor type {self.make} isn't supported")

    def get_relative_altitude(self, alt_source):
        raise ParsingError(f"Couldn't extract relative altitude. Sensor type {self.make} isn't supported")
    

class SenteraParser(Parser):
    def __init__(self, exif_data, xmp_data, make, model, path):
        super().__init__(exif_data, xmp_data, make, model, path)

    def get_timestamp(self, format_string="%Y:%m:%d %H:%M:%S"):
        try:
            datetime_obj = datetime.strptime(
                self.exif_data["EXIF DateTimeOriginal"].values, format_string
            )
        except ValueError:
            raise ParsingError("Couldn't parse found timestamp with given format string")

        return pytz.utc.localize(datetime_obj)

    def get_roll_pitch_yaw(self):
        roll = float(self.xmp_data["Camera:Roll"])
        pitch = float(self.xmp_data["Camera:Pitch"])
        yaw = float(self.xmp_data["Camera:Yaw"])
        return roll, pitch, yaw

    def get_pixel_pitch(self):
        return 1 / convert_to_float(self.exif_data["EXIF FocalPlaneXResolution"]) / 100

    def get_focal_length(self, use_calibrated=False):
        if use_calibrated:
            try:
                return float(self.xmp_data["Camera:PerspectiveFocalLength"]) / 1000
            except KeyError:
                logger.warning(
                    "Perspective focal length not found in XMP. Defaulting to uncalibrated focal length."
                )

        return super().get_focal_length()

    def _parse_session_alt(self):
        imagery_dir = os.path.dirname(self.path)
        session_path = os.path.join(imagery_dir, "session.txt")
        if not os.path.isfile(session_path):
            raise ParsingError("Couldn't find session.txt file in image directory")

        session_file = open(session_path, "r")
        session_alt = session_file.readline().split("\n")[0].split("=")[1]
        session_file.close()
        if not session_alt:
            raise ParsingError("Couldn't parse session altitude from session.txt")

        abs_alt = self.get_altitude_msl()
        return abs_alt - float(session_alt)

    def get_relative_altitude(self, alt_source):
        if alt_source == "lrf":
            try:
                try:
                    return float(self.xmp_data["Sentera:AltimeterCalculatedAGL"])
                except KeyError:
                    # l was left out in Quad v1.0.0
                    return float(self.xmp_data["Sentera:AltimeterCalcuatedAGL"])
            except KeyError:
                logger.warning(
                    "Altimeter calculated altitude not found in XMP. Defaulting to relative altitude."
                )

        try:
            return float(self.xmp_data["Camera:AboveGroundAltitude"])
        except KeyError:
            logger.warning(
                "Relative altitude not found in XMP. Attempting to parse from session.txt file."
            )
            return self._parse_session_alt()


class DJIParser(Parser):
    def __init__(self, exif_data, xmp_data, make, model, path):
        super().__init__(exif_data, xmp_data, make, model, path)

        self.pixel_pitches = {
            "FC6310": 2.41e-06,
            "FC6310S": 2.41e-06,
            "FC220": 1.55e-06,
            "FC6520": 3.4e-06,
            "FC330": 1.57937e-06,
            "FC300X": 1.57937e-06,
            "FC300S": 1.57937e-06,
            "FC6510": 2.42e-06,
            "FC350": 1.57937e-06,
            "FC350Z": 1.52958e-06,
            "FC550": 3.28e-06,
            "ZenmuseP1": 4.27e-06,
        }

    def get_roll_pitch_yaw(self):
        roll = float(self.xmp_data["drone-dji:GimbalRollDegree"])
        pitch = float(self.xmp_data["drone-dji:GimbalPitchDegree"])
        # Bring pitch into aircraft pov
        pitch += 90
        yaw = float(self.xmp_data["drone-dji:GimbalYawDegree"])
        return roll, pitch, yaw

    def get_pixel_pitch(self):
        return self.pixel_pitches[self.model]

    def get_focal_length(self, use_calibrated=False):
        if use_calibrated:
            try:
                return float(self.xmp_data["drone-dji:CalibratedFocalLength"]) / 1000
            except KeyError:
                logger.warning(
                    "Perspective focal length not found in XMP. Defaulting to uncalibrated focal length."
                )

        return super().get_focal_length()

    def get_relative_altitude(self, alt_source):
        return float(self.xmp_data["drone-dji:RelativeAltitude"])


class SonyParser(Parser):
    def __init__(self, exif_data, xmp_data, make, model, path):
        super().__init__(exif_data, xmp_data, make, model, path)

        self.pixel_pitches = {"L1D-20c": 2.4e-06}

    def get_pixel_pitch(self):
        return self.pixel_pitches[self.model]


class HasselbladParser(Parser):
    def __init__(self, exif_data, xmp_data, make, model, path):
        super().__init__(exif_data, xmp_data, make, model, path)

        self.pixel_pitches = {"DSC-RX1RM2": 4.5e-06, "DSC-RX100M2": 2.41e-06}

    def get_pixel_pitch(self):
        return self.pixel_pitches[self.model]
