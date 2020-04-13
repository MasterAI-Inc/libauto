###############################################################################
#
# Copyright (c) 2017-2020 Master AI, Inc.
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from Master AI, Inc.
#
###############################################################################

import struct
import time
from itertools import count

from cio.aa_controller_v2.easyi2c_sync import (
    open_i2c,
    write_read_i2c,
    close_i2c,
    read_bits,
    write_bits,
)


MPU6050_RA_WHO_AM_I = 0x75
MPU6050_WHO_AM_I_BIT = 6
MPU6050_WHO_AM_I_LENGTH = 6
MPU6050_RA_USER_CTRL = 0x6A
MPU6050_USERCTRL_FIFO_EN_BIT = 6
MPU6050_USERCTRL_FIFO_RESET_BIT = 2
MPU6050_RA_FIFO_COUNTH = 0x72
MPU6050_RA_FIFO_R_W = 0x74

MPU6050_PACKET_SIZE = 12
MPU6050_ACCEL_CNVT = 0.000061035
MPU6050_GYRO_CNVT = 0.007633588


def who_am_i(fd):
    return read_bits(fd, MPU6050_RA_WHO_AM_I, MPU6050_WHO_AM_I_BIT, MPU6050_WHO_AM_I_LENGTH)


def set_fifo_enabled(fd, is_enabled):
    val = 1 if is_enabled else 0
    write_bits(fd, MPU6050_RA_USER_CTRL, MPU6050_USERCTRL_FIFO_EN_BIT, 1, val)


def reset_fifo(fd):
    val = 1
    write_bits(fd, MPU6050_RA_USER_CTRL, MPU6050_USERCTRL_FIFO_RESET_BIT, 1, val)


def reset_fifo_sequence(fd):
    set_fifo_enabled(fd, False)
    reset_fifo(fd)  # reset the FIFO (can only reset while it is disabled!)
    set_fifo_enabled(fd, True)


def get_fifo_length(fd):
    h, l = write_read_i2c(fd, bytes([MPU6050_RA_FIFO_COUNTH]), 2)
    return (h << 8) | l


def read_fifo_packet(fd, fifo_length):
    buf = None
    while fifo_length >= MPU6050_PACKET_SIZE:
        buf = write_read_i2c(fd, bytes([MPU6050_RA_FIFO_R_W]), MPU6050_PACKET_SIZE)
        fifo_length -= MPU6050_PACKET_SIZE
    return buf


def run():
    fd = open_i2c(1, 0x68)

    if who_am_i(fd) != 0x34:
        raise Exception("WRONG WHO_AM_I!")

    reset_fifo_sequence(fd)

    sleep = 0.005

    for i in count():
        fifo_length = get_fifo_length(fd)
        print(fifo_length, sleep)
        if fifo_length > 200:
            reset_fifo_sequence(fd)
        elif fifo_length >= MPU6050_PACKET_SIZE:
            buf = read_fifo_packet(fd, fifo_length)
            vals = struct.unpack('>6h', buf)
            vals = [v * MPU6050_ACCEL_CNVT for v in vals[:3]] + [v * MPU6050_GYRO_CNVT for v in vals[3:]]
            print(fifo_length, ''.join([f'{v:10.3f}' for v in vals]))
            time.sleep(sleep)
            sleep *= 0.99
        else:
            sleep *= 1.01

    close_i2c(fd)


if __name__ == '__main__':
    run()

