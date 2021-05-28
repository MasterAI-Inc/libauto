###############################################################################
#
# Copyright (c) 2017-2020 Master AI, Inc.
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from Master AI, Inc.
#
###############################################################################

"""
This module talks to the IMU on the AutoAuto controller board.
"""

import struct
import time
import sys
from math import sqrt, atan2, asin, pi, radians, degrees
from itertools import count
from threading import Thread, Condition

from cio.aa_controller_v3.easyi2c_sync import (
    open_i2c,
    write_read_i2c,
    close_i2c,
    read_bits,
    write_bits,
)

from cio.aa_controller_v3 import I2C_BUS_INDEX


ICM20602_RA_WHO_AM_I = 0x75
ICM20602_WHO_AM_I_BIT = 7
ICM20602_WHO_AM_I_LENGTH = 8
WHO_AM_I_VALUE = 0x12

ICM20602_RA_USER_CTRL = 0x6A
ICM20602_USERCTRL_FIFO_EN_BIT = 6
ICM20602_USERCTRL_FIFO_RESET_BIT = 2
ICM20602_RA_FIFO_COUNTH = 0x72
ICM20602_RA_FIFO_R_W = 0x74
ICM20602_PACKET_SIZE = 12               # TODO
ICM20602_ACCEL_CNVT = 0.0001220740379   # TODO
ICM20602_GYRO_CNVT = 0.015259254738     # TODO

ICM20602_RA_PWR_MGMT_1 = 0x6B
ICM20602_PWR1_DEVICE_RESET_BIT = 7

ICM20602_RA_GYRO_CONFIG = 0x1B
ICM20602_GCONFIG_FS_SEL_BIT = 4
ICM20602_GYRO_FS_500 = 0x01
ICM20602_FCHOICE_B_BIT = 1

ICM20602_RA_ACCEL_CONFIG = 0x1C
ICM20602_ACONFIG_AFS_SEL_BIT = 4
ICM20602_ACCEL_FS_4 = 0x01

ICM20602_RA_CONFIG = 0x1A
ICM20602_CFG_DLPF_CFG_BIT = 2

ICM20602_RA_SMPLRT_DIV = 0x19

ICM20602_RA_INT_PIN_CFG = 0x37
ICM20602_INTCFG_INT_LEVEL_BIT = 7
ICM20602_INTCFG_INT_OPEN_BIT = 6
ICM20602_INTCFG_LATCH_INT_EN_BIT = 5

ICM20602_RA_INT_ENABLE = 0x38
ICM20602_DATA_READY_BIT = 0

ICM20602_RA_FIFO_EN = 0x23
ICM20602_ACCEL_FIFO_EN_BIT = 3
ICM20602_GYRO_FIFO_EN_BIT = 4

#ICM20602_


COND = Condition()
DATA = None


def who_am_i(fd):
    return read_bits(fd, ICM20602_RA_WHO_AM_I, ICM20602_WHO_AM_I_BIT, ICM20602_WHO_AM_I_LENGTH)


def set_fifo_enabled(fd, is_enabled):
    val = 1 if is_enabled else 0
    write_bits(fd, ICM20602_RA_USER_CTRL, ICM20602_USERCTRL_FIFO_EN_BIT, 1, val)


def reset_fifo(fd):
    val = 1
    write_bits(fd, ICM20602_RA_USER_CTRL, ICM20602_USERCTRL_FIFO_RESET_BIT, 1, val)


def reset_fifo_sequence(fd):
    set_fifo_enabled(fd, False)
    reset_fifo(fd)  # reset the FIFO (can only reset while it is disabled!)
    set_fifo_enabled(fd, True)


def get_fifo_length(fd):
    h, l = write_read_i2c(fd, bytes([ICM20602_RA_FIFO_COUNTH]), 2)
    return (h << 8) | l


def read_fifo_packet(fd, fifo_length):
    buf = None
    while fifo_length >= ICM20602_PACKET_SIZE:
        buf = write_read_i2c(fd, bytes([ICM20602_RA_FIFO_R_W]), ICM20602_PACKET_SIZE)
        fifo_length -= ICM20602_PACKET_SIZE
    return buf


def reset_imu(fd):
    """Resets all register on the IMU to their defaults"""
    write_bits(fd, ICM20602_RA_PWR_MGMT_1, ICM20602_PWR1_DEVICE_RESET_BIT, 1, 1)


def set_full_scale_range(fd):
    gyro_fsr = ICM20602_GYRO_FS_500   # 500 deg/second
    accel_fsr = ICM20602_ACCEL_FS_4   # +-4g
    write_bits(fd, ICM20602_RA_GYRO_CONFIG, ICM20602_GCONFIG_FS_SEL_BIT, 2, gyro_fsr)
    write_bits(fd, ICM20602_RA_ACCEL_CONFIG, ICM20602_ACONFIG_AFS_SEL_BIT, 2, accel_fsr)


def set_digital_low_pass_filter(fd):
    mode = 0
    write_bits(fd, ICM20602_RA_GYRO_CONFIG, ICM20602_FCHOICE_B_BIT, 2, mode)
    mode = 3
    write_bits(fd, ICM20602_RA_CONFIG, ICM20602_CFG_DLPF_CFG_BIT, 3, mode)


def set_sample_rate(fd):
    denom = 10    # 100Hz sample rate (1kHz / denom)
    write_bits(fd, ICM20602_RA_SMPLRT_DIV, 7, 8, denom - 1)


def set_interrupt(fd):
    mode = 1  # interrupt is active-low
    write_bits(fd, ICM20602_RA_INT_PIN_CFG, ICM20602_INTCFG_INT_LEVEL_BIT, 1, mode)

    mode = 1  # interrupt is open-drain
    write_bits(fd, ICM20602_RA_INT_PIN_CFG, ICM20602_INTCFG_INT_OPEN_BIT, 1, mode)

    mode = 0  # interrupt is latched for 50uS
    write_bits(fd, ICM20602_RA_INT_PIN_CFG, ICM20602_INTCFG_LATCH_INT_EN_BIT, 1, mode)

    mode = 1  # enable interrupts for "data ready"
    write_bits(fd, ICM20602_RA_INT_ENABLE, ICM20602_DATA_READY_BIT, 1, mode)


def enable_fifo(fd):
    mode = 1  # enable accel data (6 bytes)
    write_bits(fd, ICM20602_RA_FIFO_EN, ICM20602_ACCEL_FIFO_EN_BIT, 1, mode)

    mode = 1  # enable gyro data (6 bytes)
    write_bits(fd, ICM20602_RA_FIFO_EN, ICM20602_GYRO_FIFO_EN_BIT, 1, mode)


def set_accel_offset(fd):
    pass
    #imu.setXAccelOffset(xAccelOffset)
    #imu.setYAccelOffset(yAccelOffset)
    #imu.setZAccelOffset(zAccelOffset)


def set_gyro_offset(fd):
    pass
    #imu.setXGyroOffset(xGyroOffset)
    #imu.setYGyroOffset(yGyroOffset)
    #imu.setZGyroOffset(zGyroOffset)


def madgwick_update(accel, gyro, q, deltat):
    """
    Refs:
     - https://courses.cs.washington.edu/courses/cse466/14au/labs/l4/l4.html
     - https://courses.cs.washington.edu/courses/cse466/14au/labs/l4/MPU6050IMU.ino
     - https://x-io.co.uk/open-source-imu-and-ahrs-algorithms/
     - https://github.com/TobiasSimon/MadgwickTests
    """
    beta = 0.05    # free parameter that can be tuned; this one merges accelerometer data with the gyro data
    zeta = 0.001   # free parameter that can be tuned; this one accounts to gyro bias

    # short name local variable for readability
    ax, ay, az = accel
    gx, gy, gz = [radians(v) for v in gyro]
    q1, q2, q3, q4 = q

    #float norm;                                               // vector norm
    #float f1, f2, f3;                                         // objetive funcyion elements
    #float J_11or24, J_12or23, J_13or22, J_14or21, J_32, J_33; // objective function Jacobian elements
    #float qDot1, qDot2, qDot3, qDot4;
    #float hatDot1, hatDot2, hatDot3, hatDot4;
    #float gerrx, gerry, gerrz, gbiasx, gbiasy, gbiasz;        // gyro bias error

    # Auxiliary variables to avoid repeated arithmetic
    _halfq1 = 0.5 * q1
    _halfq2 = 0.5 * q2
    _halfq3 = 0.5 * q3
    _halfq4 = 0.5 * q4
    _2q1 = 2.0 * q1
    _2q2 = 2.0 * q2
    _2q3 = 2.0 * q3
    _2q4 = 2.0 * q4
    _2q1q3 = 2.0 * q1 * q3
    _2q3q4 = 2.0 * q3 * q4

    # Normalise accelerometer measurement
    norm = sqrt(ax * ax + ay * ay + az * az);
    if norm > 0.0:
        norm = 1.0/norm
        ax *= norm
        ay *= norm
        az *= norm

    # Compute the objective function and Jacobian
    f1 = _2q2 * q4 - _2q1 * q3 - ax
    f2 = _2q1 * q2 + _2q3 * q4 - ay
    f3 = 1.0 - _2q2 * q2 - _2q3 * q3 - az
    J_11or24 = _2q3
    J_12or23 = _2q4
    J_13or22 = _2q1
    J_14or21 = _2q2
    J_32 = 2.0 * J_14or21
    J_33 = 2.0 * J_11or24

    # Compute the gradient (matrix multiplication)
    hatDot1 = J_14or21 * f2 - J_11or24 * f1
    hatDot2 = J_12or23 * f1 + J_13or22 * f2 - J_32 * f3
    hatDot3 = J_12or23 * f2 - J_33 *f3 - J_13or22 * f1
    hatDot4 = J_14or21 * f1 + J_11or24 * f2

    # Normalize the gradient
    norm = sqrt(hatDot1 * hatDot1 + hatDot2 * hatDot2 + hatDot3 * hatDot3 + hatDot4 * hatDot4)
    hatDot1 /= norm
    hatDot2 /= norm
    hatDot3 /= norm
    hatDot4 /= norm

    # Compute estimated gyroscope biases
    gerrx = _2q1 * hatDot2 - _2q2 * hatDot1 - _2q3 * hatDot4 + _2q4 * hatDot3
    gerry = _2q1 * hatDot3 + _2q2 * hatDot4 - _2q3 * hatDot1 - _2q4 * hatDot2
    gerrz = _2q1 * hatDot4 - _2q2 * hatDot3 + _2q3 * hatDot2 - _2q4 * hatDot1

    # Compute and remove gyroscope biases
    gbiasx = gerrx * deltat * zeta
    gbiasy = gerry * deltat * zeta
    gbiasz = gerrz * deltat * zeta
    gx -= gbiasx
    gy -= gbiasy
    gz -= gbiasz

    # Compute the quaternion derivative
    qDot1 = -_halfq2 * gx - _halfq3 * gy - _halfq4 * gz
    qDot2 =  _halfq1 * gx + _halfq3 * gz - _halfq4 * gy
    qDot3 =  _halfq1 * gy - _halfq2 * gz + _halfq4 * gx
    qDot4 =  _halfq1 * gz + _halfq2 * gy - _halfq3 * gx

    # Compute then integrate estimated quaternion derivative
    q1 += (qDot1 -(beta * hatDot1)) * deltat
    q2 += (qDot2 -(beta * hatDot2)) * deltat
    q3 += (qDot3 -(beta * hatDot3)) * deltat
    q4 += (qDot4 -(beta * hatDot4)) * deltat

    # Normalize the quaternion
    norm = sqrt(q1 * q1 + q2 * q2 + q3 * q3 + q4 * q4)
    norm = 1.0/norm
    q[0] = q1 * norm
    q[1] = q2 * norm
    q[2] = q3 * norm
    q[3] = q4 * norm
    return q


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


def rotate_ahrs(accel, gyro):
    """
    Rotate the axes so that the roll/pitch/yaw
    calculations result in the *expected* roll/pitch/yaw
    orientation that is common for vehicles.
    See:
     - https://en.wikipedia.org/wiki/Euler_angles#Tait%E2%80%93Bryan_angles
    """
    ax, ay, az = accel
    gx, gy, gz = gyro
    accel = -ay, ax, az
    gyro  = -gy, gx, gz
    return accel, gyro


def run(verbose=False):
    if verbose:
        print('Will open...')

    fd = open_i2c(I2C_BUS_INDEX, 0x68)

    if verbose:
        print('Did open!')

    try:
        _handle_fd(fd, verbose)
    finally:
        close_i2c(fd)


def _handle_fd(fd, verbose):
    global DATA

    if who_am_i(fd) != WHO_AM_I_VALUE:
        raise Exception("WRONG WHO_AM_I!")

    if verbose:
        print('Will setup...')

    _setup(fd)

    if verbose:
        print('Did setup!')

    curr_time = 0       # microseconds
    dt = 1000000 // 100  # data streams at 100Hz
    dt_s = dt / 1000000

    gyro_accum = [0.0, 0.0, 0.0]
    quaternion = [1.0, 0.0, 0.0, 0.0]

    sleep = 0.005

    status = 'needs_reset'   # one of: 'needs_reset', 'did_reset', 'waiting', 'data'

    for i in count():
        status, buf = _get_buf(fd, status)
        if status == 'did_reset':
            sleep = 0.005
        elif status == 'waiting':
            sleep *= 0.99
        elif status == 'data':
            t = time.time()
            vals = struct.unpack('>6h', buf)
            vals = [v * ICM20602_ACCEL_CNVT for v in vals[:3]] + [v * ICM20602_GYRO_CNVT for v in vals[3:]]
            if verbose:
                print(f'{sleep:.4f}', ''.join([f'{v:10.3f}' for v in vals]))
            accel = vals[:3]
            gyro = vals[3:]
            gyro_accum = [(a + b*dt_s) for a, b in zip(gyro_accum, gyro)]
            ahrs = roll_pitch_yaw(madgwick_update(*rotate_ahrs(accel, gyro), quaternion, dt_s))
            with COND:
                DATA = {
                    'timestamp': curr_time,
                    'accel': accel,
                    'gyro': gyro,
                    'gyro_accum': gyro_accum,
                    'ahrs': ahrs,
                }
                if verbose:
                    print(DATA)
                COND.notify_all()
            curr_time += dt
            s = dt_s - (time.time() - t) - sleep
            if s > 0.0:
                time.sleep(s)
            sleep *= 1.01


def _get_buf(fd, status):
    try:
        if status == 'needs_reset':
            reset_fifo_sequence(fd)
            return 'did_reset', None
        elif status in ('did_reset', 'waiting', 'data'):
            fifo_length = get_fifo_length(fd)
            print(fifo_length)
            if fifo_length > 200:
                reset_fifo_sequence(fd)
                return 'did_reset', None
            elif fifo_length >= ICM20602_PACKET_SIZE:
                buf = read_fifo_packet(fd, fifo_length)
                return 'data', buf
            else:
                return 'waiting', None
        else:
            raise Exception('unreachable')
    except OSError:
        print('IMU OSError', file=sys.stderr)
        return 'needs_reset', None


def _setup(fd):
    reset_imu(fd)
    time.sleep(0.1)
    set_full_scale_range(fd)
    set_digital_low_pass_filter(fd)
    set_sample_rate(fd)
    set_interrupt(fd)
    enable_fifo(fd)
    set_accel_offset(fd)
    set_gyro_offset(fd)
    reset_fifo_sequence(fd)


def start_thread():
    thread = Thread(target=run)
    thread.daemon = True
    thread.start()
    return thread


if __name__ == '__main__':
    run(verbose=True)

