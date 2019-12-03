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


class GpioPinRef:

    def __init__(self, fd, reg_num, pin_index):
        self.fd = fd
        self.reg_num = reg_num
        self.pin_index = pin_index
        self.employ()

    @i2c_retry(N_I2C_TRIES)
    def employ(self):
        status, = write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x00, self.pin_index], 1)
        return status == 1

    @i2c_retry(N_I2C_TRIES)
    def retire(self):
        status, = write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x01, self.pin_index], 1)
        return status == 1

    @i2c_retry(N_I2C_TRIES)
    def set_output(self, high, set_pin_mode=True):  # If you know the pin is already in output mode, you should specify `set_pin_mode=False`.
        if set_pin_mode:
            instruction = 0x02 if not high else 0x03
        else:
            instruction = 0x04 if not high else 0x05
        status, = write_read_i2c_with_integrity(self.fd, [self.reg_num, instruction, self.pin_index], 1)
        if status != 1:
            raise Exception("failed to set pin as output")

    @i2c_retry(N_I2C_TRIES)
    def set_mode_input(self, with_pullup_resistor=False):
        instruction = 0x06 if not with_pullup_resistor else 0x07
        status, = write_read_i2c_with_integrity(self.fd, [self.reg_num, instruction, self.pin_index], 1)
        if status != 1:
            raise Exception("failed to set pin as input")

    @i2c_retry(N_I2C_TRIES)
    def digital_read(self):
        val, = write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x08, self.pin_index], 1)
        return val == 1

    def analog_read(self):
        @i2c_retry(N_I2C_TRIES)
        def internal_analog_read():
            lsb, msb = write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x09, self.pin_index], 2)
            return (msb << 8) | lsb
        while True:
            val = internal_analog_read()
            if val == 0xC000:
                raise Exception("This pin cannot do analog input!")
            elif val != 0x8000:
                return 5.0 * val / 1023.0

    @i2c_retry(N_I2C_TRIES)
    def get_state(self):
        state, = write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x0a, self.pin_index], 1)
        return state

    def get_state_as_string(self):
        state = self.get_state()
        value = state & 0x01
        direction = state & 0x02
        if direction:
            return "output {}".format("HIGH" if value else "LOW")
        else:
            if value:
                return "input  WITH pullup"
            else:
                return "input"


class GpioPassthrough:

    def __init__(self, fd, reg_num):
        self.fd = fd
        self.reg_num = reg_num

    def employ_pin(self, pin_index):
        return GpioPinRef(self.fd, self.reg_num, pin_index)

    def print_all_state(self, n_pins=32):
        for i in range(n_pins):
            p = self.employ_pin(i)
            print("Pin {:2d} state: {}".format(i, p.get_state_as_string()))
            p.retire()


class Timer1PWM:

    def __init__(self, fd, reg_num):
        self.fd = fd
        self.reg_num = reg_num

    @i2c_retry(N_I2C_TRIES)
    def set_top(self, value):
        status, = write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x00, (value & 0xFF), ((value >> 8) & 0xFF)], 1)
        if status != 7:
            raise Exception("failed to set_top")

    @i2c_retry(N_I2C_TRIES)
    def set_ocr_a(self, value):
        status, = write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x01, (value & 0xFF), ((value >> 8) & 0xFF)], 1)
        if status != 7:
            raise Exception("failed to set_ocr_a")

    @i2c_retry(N_I2C_TRIES)
    def enable_a(self):
        status, = write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x02], 1)
        if status != 7:
            raise Exception("failed to enable_a")

    @i2c_retry(N_I2C_TRIES)
    def disable_a(self):
        status, = write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x03], 1)
        if status != 7:
            raise Exception("failed to disable_a")

    @i2c_retry(N_I2C_TRIES)
    def set_ocr_b(self, value):
        status, = write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x04, (value & 0xFF), ((value >> 8) & 0xFF)], 1)
        if status != 7:
            raise Exception("failed to set_ocr_b")

    @i2c_retry(N_I2C_TRIES)
    def enable_b(self):
        status, = write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x05], 1)
        if status != 7:
            raise Exception("failed to enable_b")

    @i2c_retry(N_I2C_TRIES)
    def disable_b(self):
        status, = write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x06], 1)
        if status != 7:
            raise Exception("failed to disable_b")

    @i2c_retry(N_I2C_TRIES)
    def set_ocr_c(self, value):
        status, = write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x07, (value & 0xFF), ((value >> 8) & 0xFF)], 1)
        if status != 7:
            raise Exception("failed to set_ocr_c")

    @i2c_retry(N_I2C_TRIES)
    def enable_c(self):
        status, = write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x08], 1)
        if status != 7:
            raise Exception("failed to enable_c")

    @i2c_retry(N_I2C_TRIES)
    def disable_c(self):
        status, = write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x09], 1)
        if status != 7:
            raise Exception("failed to disable_c")

    @i2c_retry(N_I2C_TRIES)
    def enable(self):
        status, = write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x0a], 1)
        if status != 7:
            raise Exception("failed to enable")

    @i2c_retry(N_I2C_TRIES)
    def disable(self):
        status, = write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x0b], 1)
        if status != 7:
            raise Exception("failed to disable")


class Timer3PWM:

    def __init__(self, fd, reg_num):
        self.fd = fd
        self.reg_num = reg_num
        self.min_ocr = 0
        self.max_ocr = 20000

    @i2c_retry(N_I2C_TRIES)
    def set_top(self, value):
        status, = write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x00, (value & 0xFF), ((value >> 8) & 0xFF)], 1)
        if status != 8:
            raise Exception("failed to set_top")

    @i2c_retry(N_I2C_TRIES)
    def set_ocr(self, value):
        status, = write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x01, (value & 0xFF), ((value >> 8) & 0xFF)], 1)
        if status != 8:
            raise Exception("failed to set_ocr")

    @i2c_retry(N_I2C_TRIES)
    def enable(self):
        status, = write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x02], 1)
        if status != 8:
            raise Exception("failed to enable")

    @i2c_retry(N_I2C_TRIES)
    def disable(self):
        status, = write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x03], 1)
        if status != 8:
            raise Exception("failed to disable")

    def set_range(self, min_ocr, max_ocr):
        self.min_ocr = min_ocr
        self.max_ocr = max_ocr

    def set_pct(self, pct=0.5):
        pct = max(min(pct, 1.0), 0.0)
        value = int(round((self.max_ocr - self.min_ocr) * pct + self.min_ocr))
        self.set_ocr(value)

