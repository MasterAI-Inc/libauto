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
import asyncio
from itertools import count

from cio.aa_controller_v2.easyi2c import (
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


async def who_am_i(fd):
    return await read_bits(fd, MPU6050_RA_WHO_AM_I, MPU6050_WHO_AM_I_BIT, MPU6050_WHO_AM_I_LENGTH)


async def set_fifo_enabled(fd, is_enabled):
    val = 1 if is_enabled else 0
    await write_bits(fd, MPU6050_RA_USER_CTRL, MPU6050_USERCTRL_FIFO_EN_BIT, 1, val)


async def reset_fifo(fd):
    val = 1
    await write_bits(fd, MPU6050_RA_USER_CTRL, MPU6050_USERCTRL_FIFO_RESET_BIT, 1, val)


async def reset_fifo_sequence(fd):
    await set_fifo_enabled(fd, False)
    await reset_fifo(fd)  # reset the FIFO (can only reset while it is disabled!)
    await set_fifo_enabled(fd, True)


async def get_fifo_length(fd):
    h, l = await write_read_i2c(fd, bytes([MPU6050_RA_FIFO_COUNTH]), 2)
    return (h << 8) | l


async def read_fifo_packet(fd, fifo_length):
    buf = None
    while fifo_length >= MPU6050_PACKET_SIZE:
        buf = await write_read_i2c(fd, bytes([MPU6050_RA_FIFO_R_W]), MPU6050_PACKET_SIZE)
        fifo_length -= MPU6050_PACKET_SIZE
    return buf


async def run():
    fd = await open_i2c(1, 0x68)

    if await who_am_i(fd) != 0x34:
        raise Exception("WRONG WHO_AM_I!")

    await reset_fifo_sequence(fd)

    for i in count():
        fifo_length = await get_fifo_length(fd)
        if fifo_length > 200:
            await reset_fifo_sequence(fd)
        elif fifo_length >= MPU6050_PACKET_SIZE:
            buf = await read_fifo_packet(fd, fifo_length)
            vals = struct.unpack('>6h', buf)
            vals = [v * MPU6050_ACCEL_CNVT for v in vals[:3]] + [v * MPU6050_GYRO_CNVT for v in vals[3:]]
            print(fifo_length, ''.join([f'{v:10.3f}' for v in vals]))

    await close_i2c(fd)


if __name__ == '__main__':
    asyncio.run(run())

