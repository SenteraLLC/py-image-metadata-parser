"""Math used to handle gimbal lock/singularity."""

from collections import namedtuple
from math import asin, atan2, cos, pi, sin

Quaternion = namedtuple("Quaternion", "q0 q1 q2 q3")


def euler_to_quaternion(roll, pitch, yaw):
    """Convert Euler angles to quaternions."""
    # Intermediate calculations for 'cos(x/2)' of Euler angles.
    cos_y = cos((yaw * pi) / 360.0)
    cos_p = cos((pitch * pi) / 360.0)
    cos_r = cos((roll * pi) / 360.0)

    # Intermediate calculations for 'sin(x/2)' of Euler angles.
    sin_y = sin((yaw * pi) / 360.0)
    sin_p = sin((pitch * pi) / 360.0)
    sin_r = sin((roll * pi) / 360.0)

    q0 = cos_r * cos_p * cos_y + sin_r * sin_p * sin_y
    q1 = sin_r * cos_p * cos_y - cos_r * sin_p * sin_y
    q2 = cos_r * sin_p * cos_y + sin_r * cos_p * sin_y
    q3 = cos_r * cos_p * sin_y - sin_r * sin_p * cos_y

    return Quaternion(q0, q1, q2, q3)


def quaternion_to_euler(q):
    """Convert quaternions to Euler angles."""
    # Compute pitch sine term.
    sin_p = 2.0 * (q.q0 * q.q2 - q.q3 * q.q1)

    # Pitch >= 89.0 deg ( gimbal lock condition ) ?
    if sin_p >= 0.99985:
        y = -2 * atan2(q.q1, q.q0)
        p = pi / 2
        r = 0.0
    # Pitch <= -89.0 deg ( gimbal lock condition ) ?
    elif sin_p <= -0.99985:
        y = 2 * atan2(q.q1, q.q0)
        p = -pi / 2
        r = 0.0
    # No gimbal - lock condition ?
    else:
        # yaw.
        sin_y = 2.0 * (q.q0 * q.q3 + q.q1 * q.q2)
        cos_y = 1.0 - 2.0 * (q.q2 * q.q2 + q.q3 * q.q3)
        y = atan2(sin_y, cos_y)

        # pitch.
        p = asin(sin_p)

        # roll.
        sin_r = 2.0 * (q.q0 * q.q1 + q.q2 * q.q3)
        cos_r = 1.0 - 2.0 * (q.q1 * q.q1 + q.q2 * q.q2)
        r = atan2(sin_r, cos_r)

    # Convert to degrees.
    y *= 180.0 / pi
    p *= 180.0 / pi
    r *= 180.0 / pi

    return r, p, y


def constrain_roll_pitch_yaw(roll, pitch, yaw):
    """
    Constrain roll, pitch, yaw values to what we expect.

    At pitch = +-90, a singularity can occur (multiple solutions for the same orientation).
    We convert the euler angles to quaternions and back to ensure a well defined output
    around these singularity values.
    """
    return quaternion_to_euler(euler_to_quaternion(roll, pitch, yaw))
