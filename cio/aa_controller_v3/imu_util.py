###############################################################################
#
# Copyright (c) 2017-2023 Master AI, Inc.
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from Master AI, Inc.
#
###############################################################################

from math import atan2, asin, pi, degrees


def roll_pitch_yaw(q):
    """
    Refs:
     - https://en.wikipedia.org/wiki/Euler_angles#Tait%E2%80%93Bryan_angles
     - https://en.wikipedia.org/wiki/Conversion_between_quaternions_and_Euler_angles
    """
    qw, qx, qy, qz = q

    # roll (x-axis rotation)
    sinr_cosp = 2.0 * (qw * qx + qy * qz)
    cosr_cosp = 1.0 - 2.0 * (qx * qx + qy * qy)
    roll = atan2(sinr_cosp, cosr_cosp)

    # pitch (y-axis rotation)
    sinp = 2.0 * (qw * qy - qz * qx)
    if abs(sinp) >= 1.0:
        pitch = (pi if sinp > 0.0 else -pi) / 2.0   # use 90 degrees if out of range
    else:
        pitch = asin(sinp)

    # yaw (z-axis rotation)
    siny_cosp = 2.0 * (qw * qz + qx * qy)
    cosy_cosp = 1.0 - 2.0 * (qy * qy + qz * qz)
    yaw = atan2(siny_cosp, cosy_cosp)

    # Convert to degrees:
    roll = degrees(roll)
    pitch = degrees(pitch)
    yaw = degrees(yaw)
    return roll, pitch, yaw
