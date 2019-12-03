###############################################################################
#
# Copyright (c) 2017-2018 AutoAuto, LLC
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from AutoAuto, LLC.
#
###############################################################################

"""
It turns out that Linux has simple support for I2C (no need for anything fancy).
And we can invoke the necessary system calls from python, so it's all quite easy!

See: [Linux I2C Interface](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/Documentation/i2c/dev-interface) (alternate source: [here](https://github.com/torvalds/linux/blob/master/Documentation/i2c/dev-interface))

Also note: You'll see above there's an SMBus interface in the Linux interface linked above.
We find that we can't use that because we need to send more than two bytes of data per message
(and the SMBus interface supports at most "word" reads and writes). But, Linux provides more
general read/write calls so we can send as many bytes as we want per message. For the same
reason, we can't use the SMBus python wrapper because it has the same limitation. That said,
this _alternate_ SMBus python wrapper (named "smbus2") is a good reference for how to do a
lot of cool Linux system calls through python. [link](https://pypi.python.org/pypi/smbus2/0.1.2)
[link](https://github.com/kplindegaard/smbus2/blob/master/smbus2/smbus2.py)
"""

import os
import time
import errno
from fcntl import ioctl
from functools import wraps

from . import integrity


def open_i2c(device_index, slave_address):
    """
    Open and configure a file description to the given
    slave (`slave_address`) over the given Linux device
    interface index (`device_index`).
    """
    path = "/dev/i2c-{}".format(device_index)
    flags = os.O_RDWR
    fd = os.open(path, flags)            # <-- throws if fails
    I2C_SLAVE = 0x0703                   # <-- a constant from `linux/i2c-dev.h`.
    ioctl(fd, I2C_SLAVE, slave_address)  # <-- throws if fails
    return fd


def read_i2c(fd, n):
    """
    Read `n` bytes from the I2C slave connected to `fd`.
    """
    buf = os.read(fd, n)  # <-- throws if fails, but not if short read
    if len(buf) != n:
        raise OSError(errno.EIO, os.strerror(errno.EIO))
    return buf


def write_i2c(fd, buf):
    """
    Write the `buf` (a `bytes`-buffer) to the I2C slave at `fd`.
    """
    w = os.write(fd, buf)  # <-- throws if fails, but not if short write
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
    write_i2c(fd, bytes(write_buf))
    return read_i2c(fd, read_len)


def write_read_i2c_with_integrity(fd, write_buf, read_len):
    """
    Same as `write_read_i2c` but uses integrity checks for
    both the outgoing and incoming buffers. See the `integrity`
    module for details on how this works.
    """
    read_len = integrity.read_len_with_integrity(read_len)
    write_buf = integrity.put_integrity(write_buf)
    write_i2c(fd, write_buf)
    read_buf = read_i2c(fd, read_len)
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


def i2c_reliability_test(func, iterations=1000):
    """
    Call `func` repeatedly to get a feel for its reliability.
    It will be called `iterations` number of times, and it
    is assumed to work as long as it doesn't raise `OSError`.
    A short report is printed to summarize its reliability.
    """
    num_fails = 0
    for _ in range(iterations):
        try:
            func()
        except OSError:
            num_fails += 1
    return "{} fails ({:.2f}%) of {} iterations" \
            .format(num_fails, num_fails / iterations * 100, iterations)

