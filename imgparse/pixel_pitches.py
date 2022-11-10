"""
Lookup tables for DJI, Sony, and Hasselblad pixel pitches.

None of these camera types store the pixel pitch in xmp or exif tags, so they need to be manually coded and accessed.

To add a new supported camera make, create a new dictionary of camera model/pixel pitch pairs, then add dictionary
to ``PIXEL_PITCHES``, indexed by camera make.

To add a new supported camera model, simply append a new model/pixel pitch pair to the existing camera make dictionary.
"""

DJI_PIXEL_PITCH = {
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
    "FC3170": 8e-07,
    "M3E": 3.28e-06,
}

HASSELBLAD_PIXEL_PITCH = {"L1D-20c": 2.4e-06}

SONY_PIXEL_PITCH = {"DSC-RX1RM2": 4.5e-06, "DSC-RX100M2": 2.41e-06}

PIXEL_PITCHES = {
    "DJI": DJI_PIXEL_PITCH,
    "Hasselblad": HASSELBLAD_PIXEL_PITCH,
    "SONY": SONY_PIXEL_PITCH,
}
