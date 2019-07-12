"""
Lookup tables for DJI and Hasselblad pixel pitches.  Neither camera types store the pixel pitch in image metadata, so
they need to be manually coded and accessed.
"""

DJI_PIXEL_PITCH = {'FC6310': 2.41e-06, 'FC6310S': 2.41e-06, 'FC220': 1.55e-06, 'FC6520': 3.4e-06, 'FC330': 1.57937e-06,
                   'FC300X': 1.57937e-06, 'FC300S': 1.57937e-06}

HASSELBLAD_PIXEL_PITCH = {'L1D-20c': 2.4e-06}
