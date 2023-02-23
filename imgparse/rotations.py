"""Math used to handle gimbal lock/singularity."""

from collections import namedtuple
from math import asin, atan2, cos, pi, sin

Quaternion = namedtuple("Quaternion", "q0 q1 q2 q3")
Euler = namedtuple("Euler", "r p y")


def euler_to_quaternion(e: Euler):
    """Convert Euler angles to quaternions."""
    # Intermediate calculations for 'cos(x/2)' of Euler angles.
    cos_y = cos((e.y * pi) / 360.0)
    cos_p = cos((e.p * pi) / 360.0)
    cos_r = cos((e.r * pi) / 360.0)

    # Intermediate calculations for 'sin(x/2)' of Euler angles.
    sin_y = sin((e.y * pi) / 360.0)
    sin_p = sin((e.p * pi) / 360.0)
    sin_r = sin((e.r * pi) / 360.0)

    q0 = cos_r * cos_p * cos_y + sin_r * sin_p * sin_y
    q1 = sin_r * cos_p * cos_y - cos_r * sin_p * sin_y
    q2 = cos_r * sin_p * cos_y + sin_r * cos_p * sin_y
    q3 = cos_r * cos_p * sin_y - sin_r * sin_p * cos_y

    return Quaternion(q0, q1, q2, q3)


def quaternion_to_euler(q: Quaternion):
    """Convert quaternions to Euler angles."""
    # Compute pitch sine term.
    sin_p = 2.0 * (q.q0 * q.q2 - q.q3 * q.q1)

    epsilon_deg = 1
    pitch_thresh_rad = (90 - epsilon_deg) * pi / 180

    # Gimbal lock condition: pitch ~= 90 degrees
    if sin_p >= sin(pitch_thresh_rad):
        y = -2 * atan2(q.q1, q.q0)
        p = pi / 2
        r = 0.0
    # Gimbal lock condition: pitch ~= -90 degrees
    elif sin_p <= sin(-pitch_thresh_rad):
        y = 2 * atan2(q.q1, q.q0)
        p = -pi / 2
        r = 0.0
    # No gimbal lock
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

    return Euler(r, p, y)


def multiply_quaternions(q_a, q_b):
    """
    Multiply two quaternions together.

    Multiplying quaternions is the same as composing two rotations together.
    For more information: https://github.com/SenteraLLC/libRot/blob/master/inc/rot.h
    """
    # First(left) term auxiliary variables.
    a0 = q_a.q0
    a1 = q_a.q1
    a2 = q_a.q2
    a3 = q_a.q3

    # Second(right) term auxiliary variables.
    b0 = q_b.q0
    b1 = q_b.q1
    b2 = q_b.q2
    b3 = q_b.q3

    q0 = a0 * b0 - a1 * b1 - a2 * b2 - a3 * b3
    q1 = a0 * b1 + a1 * b0 + a2 * b3 - a3 * b2
    q2 = a0 * b2 + a2 * b0 + a3 * b1 - a1 * b3
    q3 = a0 * b3 + a3 * b0 + a1 * b2 - a2 * b1

    return Quaternion(q0, q1, q2, q3)


def apply_rotational_offset(attitude_e: Euler, offset_e: Euler):
    """Rotate provided attitude by offsets."""
    offset_q = euler_to_quaternion(offset_e)
    attitude_q = euler_to_quaternion(attitude_e)

    # Perform the rotation.
    result_q = multiply_quaternions(attitude_q, offset_q)

    # Convert result to Euler.
    return quaternion_to_euler(result_q)
