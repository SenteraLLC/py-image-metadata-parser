"""Containers for xmp tags for various sensors."""


class XMPTags:
    """
    Generic tags defaulting to an empty string or a common default.

    If a sensor isn't supported for a given tag, the empty string or common default will cause a KeyError
    to be thrown, the same as if a valid tag wasn't found.
    """

    RELATIVE_ALT: str = ""
    ROLL: str = ""
    PITCH: str = ""
    YAW: str = ""
    FOCAL_LEN: str = ""
    WAVELENGTH_CENTRAL: str = "Camera:CentralWavelength"
    WAVELENGTH_FWHM: str = "Camera:WavelengthFWHM"
    BANDNAME: str = "Camera:BandName"
    LRF_ALT: str = ""
    LRF_ALT2: str = ""  # See SenteraTags below
    ILS: str = "Camera:SunSensor"
    HOMEPOINT_LAT: str = ""
    HOMEPOINT_LON: str = ""
    PRINCIPAL_POINT: str = ""
    DISTORTION: str = ""
    SELF_DATA: str = ""
    IRRADIANCE: str = ""
    CAPTURE_UUID: str = ""
    FLIGHT_UUID: str = ""
    DEWARP_FLAG: str = ""
    X_ACCURACY_M: str = ""
    Y_ACCURACY_M: str = ""
    Z_ACCURACY_M: str = ""


class SenteraTags(XMPTags):
    """Sentera XMP tags."""

    RELATIVE_ALT = "Camera:AboveGroundAltitude"
    ROLL = "Camera:Roll"
    PITCH = "Camera:Pitch"
    YAW = "Camera:Yaw"
    FOCAL_LEN = "Camera:PerspectiveFocalLength"
    LRF_ALT = "Sentera:AltimeterCalculatedAGL"
    LRF_ALT2 = "Sentera:AltimeterCalcuatedAGL"  # l was left out in Quad v1.0.0
    HOMEPOINT_LAT = "SENTERA:HomePointLatitude"
    HOMEPOINT_LON = "SENTERA:HomePointLongitude"
    PRINCIPAL_POINT = "Camera:PrincipalPoint"
    DISTORTION = "Camera:PerspectiveDistortion"
    CAPTURE_UUID = "Camera:CaptureUUID"
    FLIGHT_UUID = "Camera:FlightUUID"
    X_ACCURACY_M: str = "Camera:GPSXYAccuracy"
    Y_ACCURACY_M: str = "Camera:GPSXYAccuracy"
    Z_ACCURACY_M: str = "Camera:GPSZAccuracy"


class DJITags(XMPTags):
    """DJI XMP tags."""

    RELATIVE_ALT = "drone-dji:RelativeAltitude"
    ROLL = "drone-dji:GimbalRollDegree"
    PITCH = "drone-dji:GimbalPitchDegree"
    YAW = "drone-dji:GimbalYawDegree"
    FOCAL_LEN = "drone-dji:CalibratedFocalLength"
    SELF_DATA = "drone-dji:SelfData"
    IRRADIANCE = "Camera:Irradiance"
    CAPTURE_UUID = "drone-dji:CaptureUUID"
    DEWARP_FLAG = "drone-dji:DewarpFlag"
    DISTORTION = "drone-dji:DewarpData"
    X_ACCURACY_M: str = "drone-dji:RtkStdLon"
    Y_ACCURACY_M: str = "drone-dji:RtkStdLat"
    Z_ACCURACY_M: str = "drone-dji:RtkStdHgt"


class MicaSenseTags(XMPTags):
    """MicaSense XMP Tags."""

    CAPTURE_UUID = "MicaSense:CaptureId"
    IRRADIANCE = "Camera:Irradiance"
    X_ACCURACY_M: str = "Camera:GPSXYAccuracy"
    Y_ACCURACY_M: str = "Camera:GPSXYAccuracy"
    Z_ACCURACY_M: str = "Camera:GPSZAccuracy"


class ParrotTags(XMPTags):
    """Parrot XMP Tags."""

    CAPTURE_UUID = "Camera:CaptureUUID"
