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
The synchronous version of `easyi2c`.
"""

import os
import time
import errno
from fcntl import ioctl
from functools import wraps

from . import integrity


def open_i2c(device_index, slave_address):
    """
    Open and configure a file descriptor to the given
    slave (`slave_address`) over the given Linux device
    interface index (`device_index`).
    """
    path = "/dev/i2c-{}".format(device_index)
    flags = os.O_RDWR
    fd = os.open(path, flags)
    I2C_SLAVE = 0x0703          # <-- a constant from `linux/i2c-dev.h`.
    ioctl(fd, I2C_SLAVE, slave_address)
    return fd


def close_i2c(fd):
    """
    Close a file descriptor returned by `open_i2c()`.
    """
    os.close(fd)


def _read_i2c(fd, n):
    """
    Read `n` bytes from the I2C slave connected to `fd`.
    """
    if n == 0:
        return b''
    buf = os.read(fd, n)
    if len(buf) != n:
        raise OSError(errno.EIO, os.strerror(errno.EIO))
    return buf


def _write_i2c(fd, buf):
    """
    Write the `buf` (a `bytes`-buffer) to the I2C slave at `fd`.
    """
    w = os.write(fd, buf)
    if len(buf) != w:
        raise OSError(errno.EIO, os.strerror(errno.EIO))


def write_read_i2c(fd, write_buf, read_len):
    """
    Write-to then read-from the I2C slave at `fd`.

    Note: The Pi's I2C bus isn't the best, and it fails sometimes.
          See: http://www.advamation.com/knowhow/raspberrypi/rpi-i2c-bug.html
          Therefore you will want to incorporate integrity checks
          when you read/write to the I2C bus. See the next function
          in this module for how to do this.
    """
    _write_i2c(fd, write_buf)
    return _read_i2c(fd, read_len)


def write_read_i2c_with_integrity(fd, write_buf, read_len):
    """
    Same as `write_read_i2c` but uses integrity checks for
    both the outgoing and incoming buffers. See the `integrity`
    module for details on how this works.
    """
    read_len = integrity.read_len_with_integrity(read_len)
    write_buf = integrity.put_integrity(write_buf)
    _write_i2c(fd, write_buf)
    read_buf = _read_i2c(fd, read_len)
    read_buf = integrity.check_integrity(read_buf)
    if read_buf is None:
        raise OSError(errno.ECOMM, os.strerror(errno.ECOMM))
    return read_buf


def i2c_retry(n):
    """
    Decorator for I2C-dependent functions which allows them to retry
    the I2C transaction up to `n` times before throwing an error.
    """
    def decorator(func):
        @wraps(func)
        def func_wrapper(*args, **kwargs):
            for _ in range(n-1):
                try:
                    return func(*args, **kwargs)
                except OSError:
                    time.sleep(0.05)  # <-- allow the I2C bus to chill-out before we try again
            return func(*args, **kwargs)

        return func_wrapper

    return decorator


def i2c_poll_until(func, desired_return_value, timeout_ms):
    """
    Helper for I2C-dependent functions which polls the `func`
    until its return value is the `desired_return_value`. It
    ignores other return values and exceptions while polling,
    until the `timeout_ms` is reached in which case it raises
    a `TimeoutError`. If `func` returns the `desired_return_value`
    before `timeout_ms` have elapsed, this function returns
    instead of raising.
    """
    start_time = time.time()

    while True:
        try:
            ret = func()
            if ret == desired_return_value:
                return ret, (time.time() - start_time) * 1000
        except OSError:
            pass

        if (time.time() - start_time) * 1000 > timeout_ms:
            raise TimeoutError("{} did not return {} before {} milliseconds".format(func, desired_return_value, timeout_ms))


def read_byte(fd, reg):
    """Read a single byte from the register `reg`."""
    b, = write_read_i2c(fd, bytes([reg]), 1)
    return b


def read_bits(fd, reg, bitStart, length):
    """
    Read bits from the register `reg`.
    LSB is 0. E.g.
        76543210
         ^^^          <-- bitStart=6, length=3
          ^^^^        <-- bitStart=5, length=4
    """
    b = read_byte(fd, reg)
    mask = ((1 << length) - 1) << (bitStart - length + 1)
    b &= mask;
    b >>= (bitStart - length + 1);
    return b


def write_byte(fd, reg, b):
    """Write a single byte `b` to the register `reg`."""
    write_read_i2c(fd, bytes([reg, b]), 0)


def write_bits(fd, reg, bitStart, length, data):
    """
    Write bits to the register `reg`. See `read_bits()`
    for an explanation of `bitStart` and `length`.
    """
    b = read_byte(fd, reg)
    mask = ((1 << length) - 1) << (bitStart - length + 1);
    data <<= (bitStart - length + 1);
    data &= mask;
    b &= ~(mask);
    b |= data;
    write_byte(fd, reg, b)

