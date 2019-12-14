###############################################################################
#
# Copyright (c) 2017-2018 AutoAuto, LLC
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from AutoAuto, LLC.
#
###############################################################################

from .easyi2c import (write_read_i2c_with_integrity,
                      i2c_retry)

from . import N_I2C_TRIES


class Timer1PWM:

    def __init__(self, fd, reg_num):
        self.fd = fd
        self.reg_num = reg_num

    @i2c_retry(N_I2C_TRIES)
    async def set_top(self, value):
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x00, (value & 0xFF), ((value >> 8) & 0xFF)], 1)
        if status != 7:
            raise Exception("failed to set_top")

    @i2c_retry(N_I2C_TRIES)
    async def set_ocr_a(self, value):
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x01, (value & 0xFF), ((value >> 8) & 0xFF)], 1)
        if status != 7:
            raise Exception("failed to set_ocr_a")

    @i2c_retry(N_I2C_TRIES)
    async def enable_a(self):
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x02], 1)
        if status != 7:
            raise Exception("failed to enable_a")

    @i2c_retry(N_I2C_TRIES)
    async def disable_a(self):
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x03], 1)
        if status != 7:
            raise Exception("failed to disable_a")

    @i2c_retry(N_I2C_TRIES)
    async def set_ocr_b(self, value):
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x04, (value & 0xFF), ((value >> 8) & 0xFF)], 1)
        if status != 7:
            raise Exception("failed to set_ocr_b")

    @i2c_retry(N_I2C_TRIES)
    async def enable_b(self):
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x05], 1)
        if status != 7:
            raise Exception("failed to enable_b")

    @i2c_retry(N_I2C_TRIES)
    async def disable_b(self):
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x06], 1)
        if status != 7:
            raise Exception("failed to disable_b")

    @i2c_retry(N_I2C_TRIES)
    async def set_ocr_c(self, value):
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x07, (value & 0xFF), ((value >> 8) & 0xFF)], 1)
        if status != 7:
            raise Exception("failed to set_ocr_c")

    @i2c_retry(N_I2C_TRIES)
    async def enable_c(self):
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x08], 1)
        if status != 7:
            raise Exception("failed to enable_c")

    @i2c_retry(N_I2C_TRIES)
    async def disable_c(self):
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x09], 1)
        if status != 7:
            raise Exception("failed to disable_c")

    @i2c_retry(N_I2C_TRIES)
    async def enable(self):
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x0a], 1)
        if status != 7:
            raise Exception("failed to enable")

    @i2c_retry(N_I2C_TRIES)
    async def disable(self):
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x0b], 1)
        if status != 7:
            raise Exception("failed to disable")


class Timer3PWM:

    def __init__(self, fd, reg_num):
        self.fd = fd
        self.reg_num = reg_num
        self.min_ocr = 0
        self.max_ocr = 20000

    @i2c_retry(N_I2C_TRIES)
    async def set_top(self, value):
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x00, (value & 0xFF), ((value >> 8) & 0xFF)], 1)
        if status != 8:
            raise Exception("failed to set_top")

    @i2c_retry(N_I2C_TRIES)
    async def set_ocr(self, value):
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x01, (value & 0xFF), ((value >> 8) & 0xFF)], 1)
        if status != 8:
            raise Exception("failed to set_ocr")

    @i2c_retry(N_I2C_TRIES)
    async def enable(self):
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x02], 1)
        if status != 8:
            raise Exception("failed to enable")

    @i2c_retry(N_I2C_TRIES)
    async def disable(self):
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x03], 1)
        if status != 8:
            raise Exception("failed to disable")

    async def set_range(self, min_ocr, max_ocr):
        self.min_ocr = min_ocr
        self.max_ocr = max_ocr

    async def set_pct(self, pct=0.5):
        pct = max(min(pct, 1.0), 0.0)
        value = int(round((self.max_ocr - self.min_ocr) * pct + self.min_ocr))
        self.set_ocr(value)

