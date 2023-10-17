"""
Lookup tables for DJI, Sony, and Hasselblad pixel pitches.

None of these camera types store the pixel pitch in xmp or exif tags, so they need to be manually coded and accessed.

To add a new supported camera make, create a new dictionary of camera model/pixel pitch pairs, then add dictionary
to ``PIXEL_PITCHES``, indexed by camera make.

To add a new supported camera model, simply append a new model/pixel pitch pair to the existing camera make dictionary.
"""

DJI_PIXEL_PITCH = {
    "FC6310": 2.41e-06,  # Phantom 4 Pro
    "FC6310S": 2.41e-06,  # Phantom 4 Pro V2
    "FC220": 1.55e-06,  # Phantom 2 Vision
    "FC6520": 3.4e-06,  # X5S (Inspire 2)
    "FC330": 1.57937e-06,  # Phantom 4
    "FC300X": 1.57937e-06,  # Phantom 3 (4K)
    "FC300S": 1.57937e-06,  # Phantom 3 Pro
    "FC6510": 2.42e-06,  # X4S
    "FC350": 1.57937e-06,  # X3
    "FC350Z": 1.52958e-06,  # OSMO zoom
    "FC550": 3.28e-06,  # X5 (Inspire 1)
    "ZenmuseP1": 4.27e-06,  # Zemmuse P1 (M300) (24mm, 35mm, 50mm)
    "FC3170": 8e-07,  # Mavic Air 2
    "M3E": 3.28e-06,  # Mavic 3 Enterprise
    "FC6360": 3.0e-06,  # Phantom 4 Multispectral
    "FC6310R": 2.41e-06,  # Phatom 4 Pro RTK
}

HASSELBLAD_PIXEL_PITCH = {
    "L1D-20c": 2.4e-06,  # Mavic 2 Pro
    "L2D-20c": 3.28e-06,  # Mavic 3 Classic
}

SONY_PIXEL_PITCH = {
    "DSC-RX1RM2": 4.5e-06,  # Sony Cyber-shot RX1R II (42.4MP)
    "DSC-RX100M2": 2.41e-06,  # Sony Cyber-shot DSC-RX100 II (20.2MP)
    "ILCE-7RM4A": 3.76e-06,  # Sony A7R IV (60.2MP)
}

PIXEL_PITCHES = {
    "DJI": DJI_PIXEL_PITCH,
    "Hasselblad": HASSELBLAD_PIXEL_PITCH,
    "SONY": SONY_PIXEL_PITCH,
}
