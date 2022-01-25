"""Containers for xmp tags for various sensors."""


class SensorTags:
    """
    Generic tags defaulting to None.

    If a sensor isn't supported for a given tag, None will cause a KeyError to be thrown,
    the same as if a valid tag wasn't found.
    """

    RELATIVE_ALT = None
    ROLL = None
    PITCH = None
    YAW = None
    FOCAL_LEN = None


class SenteraTags(SensorTags):
    """Sentera XMP tags."""

    RELATIVE_ALT = "Camera:AboveGroundAltitude"
    ROLL = "Camera:Roll"
    PITCH = "Camera:Pitch"
    YAW = "Camera:Yaw"
    FOCAL_LEN = "Camera:PerspectiveFocalLength"
    ILS = "Camera:SunSensor"
    LRF_ALT = "Sentera:AltimeterCalculatedAGL"
    LRF_ALT2 = "Sentera:AltimeterCalcuatedAGL"  # l was left out in Quad v1.0.0
    # WAVELENGTH_CENTRAL = "Camera:CentralWavelength"
    # WAVELENGTH_FWHM = "Camera:WavelengthFWHM"
    # BANDNAME = "Camera:BandName"


class DJITags(SensorTags):
    """DJI XMP tags."""

    RELATIVE_ALT = "drone-dji:RelativeAltitude"
    ROLL = "drone-dji:GimbalRollDegree"
    PITCH = "drone-dji:GimbalPitchDegree"
    YAW = "drone-dji:GimbalYawDegree"
    FOCAL_LEN = "drone-dji:CalibratedFocalLength"
    # SELF_DATA = "drone-dji:SelfData"


def get_tags(make):
    """Return the XMP tags based on sensor make."""
    if make == "Sentera":
        return SenteraTags
    elif make == "DJI":
        return DJITags
    else:
        return SensorTags
