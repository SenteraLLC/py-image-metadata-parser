from collections import namedtuple

Quaternion = namedtuple("Quaternion", "q0 q1 q2 q3")
Euler = namedtuple("Euler", "r p y")
Coords = namedtuple("Coords", "lat lon")
Dimensions = namedtuple("Dimensions", "height width")
