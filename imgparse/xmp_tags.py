"""Containers for xmp tags for various sensors."""


class XMPTags:
    """
    Generic tags defaulting to an empty string.

    If a sensor isn't supported for a given tag, the empty string will cause a KeyError
    to be thrown, the same as if a valid tag wasn't found.
    """

    RELATIVE_ALT: str = ""
    ROLL: str = ""
    PITCH: str = ""
    YAW: str = ""
    FOCAL_LEN: str = ""
    WAVELENGTH_CENTRAL: str = ""
    WAVELENGTH_FWHM: str = ""
    BANDNAME: str = ""
    LRF_ALT: str = ""
    LRF_ALT2: str = ""  # See SenteraTags below
    ILS: str = ""
    HOMEPOINT_LAT: str = ""
    HOMEPOINT_LON: str = ""
    PRINCIPAL_POINT: str = ""
    DISTORTION: str = ""
    SELF_DATA: str = ""
    IRRADIANCE: str = ""
    CAPTURE_UUID: str = ""
    FLIGHT_UUID: str = ""


class SenteraTags(XMPTags):
    """Sentera XMP tags."""

    RELATIVE_ALT = "Camera:AboveGroundAltitude"
    ROLL = "Camera:Roll"
    PITCH = "Camera:Pitch"
    YAW = "Camera:Yaw"
    FOCAL_LEN = "Camera:PerspectiveFocalLength"
    WAVELENGTH_CENTRAL = "Camera:CentralWavelength"
    WAVELENGTH_FWHM = "Camera:WavelengthFWHM"
    BANDNAME = "Camera:BandName"
    LRF_ALT = "Sentera:AltimeterCalculatedAGL"
    LRF_ALT2 = "Sentera:AltimeterCalcuatedAGL"  # l was left out in Quad v1.0.0
    ILS = "Camera:SunSensor"
    HOMEPOINT_LAT = "SENTERA:HomePointLatitude"
    HOMEPOINT_LON = "SENTERA:HomePointLongitude"
    PRINCIPAL_POINT = "Camera:PrincipalPoint"
    DISTORTION = "Camera:PerspectiveDistortion"
    CAPTURE_UUID = "Camera:CaptureUUID"
    FLIGHT_UUID = "Camera:FlightUUID"


class DJITags(XMPTags):
    """DJI XMP tags."""

    RELATIVE_ALT = "drone-dji:RelativeAltitude"
    ROLL = "drone-dji:GimbalRollDegree"
    PITCH = "drone-dji:GimbalPitchDegree"
    YAW = "drone-dji:GimbalYawDegree"
    FOCAL_LEN = "drone-dji:CalibratedFocalLength"
    WAVELENGTH_CENTRAL = "Camera:CentralWavelength"
    WAVELENGTH_FWHM = "Camera:WavelengthFWHM"
    BANDNAME = "Camera:BandName"
    SELF_DATA = "drone-dji:SelfData"
    ILS = "Camera:SunSensor"
    IRRADIANCE = "Camera:Irradiance"
    CAPTURE_UUID = "drone-dji:CaptureUUID"
    DEWARP_FLAG = "drone-dji:DewarpFlag"


class MicaSenseTags(XMPTags):
    """MicaSense XMP Tags."""

    WAVELENGTH_CENTRAL = "Camera:CentralWavelength"
    WAVELENGTH_FWHM = "Camera:WavelengthFWHM"
    BANDNAME = "Camera:BandName"
    CAPTURE_UUID = "MicaSense:CaptureId"
    IRRADIANCE = "Camera:Irradiance"


class ParrotTags(XMPTags):
    """Parrot XMP Tags."""

    WAVELENGTH_CENTRAL = "Camera:CentralWavelength"
    WAVELENGTH_FWHM = "Camera:WavelengthFWHM"
    BANDNAME = "Camera:BandName"
    CAPTURE_UUID = "Camera:CaptureUUID"
