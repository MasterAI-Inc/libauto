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
import asyncio
from fcntl import ioctl
from functools import wraps

from . import integrity


# It would be best to have this lock work on a per-fd basis, but we won't
# worry about that because the primary use-case will be that we have only
# one fd open to this I2C bus. Having this global lock below makes it easier
# because we don't have to pass it around everywhere the fd goes.
LOCK = None


async def open_i2c(device_index, slave_address):
    """
    Open and configure a file descriptor to the given
    slave (`slave_address`) over the given Linux device
    interface index (`device_index`).
    """
    global LOCK
    if LOCK is None:
        LOCK = asyncio.Lock()
    loop = asyncio.get_running_loop()
    path = "/dev/i2c-{}".format(device_index)
    flags = os.O_RDWR
    fd = await loop.run_in_executor(
            None,
            os.open,            # <-- throws if fails
            path, flags
    )
    I2C_SLAVE = 0x0703          # <-- a constant from `linux/i2c-dev.h`.
    await loop.run_in_executor(
            None,
            ioctl,              # <-- throws if fails
            fd, I2C_SLAVE, slave_address
    )
    return fd


async def close_i2c(fd):
    """
    Close a file descriptor returned by `open_i2c()`.
    """
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(
            None,
            os.close,            # <-- throws if fails
            fd
    )


async def _read_i2c(fd, n):
    """
    Read `n` bytes from the I2C slave connected to `fd`.
    """
    loop = asyncio.get_running_loop()
    buf = await loop.run_in_executor(
            None,
            os.read,    # <-- throws if fails, but not if short read
            fd, n
    )
    if len(buf) != n:
        raise OSError(errno.EIO, os.strerror(errno.EIO))
    return buf


async def _write_i2c(fd, buf):
    """
    Write the `buf` (a `bytes`-buffer) to the I2C slave at `fd`.
    """
    loop = asyncio.get_running_loop()
    w = await loop.run_in_executor(
            None,
            os.write,   # <-- throws if fails, but not if short write
            fd, buf
    )
    if len(buf) != w:
        raise OSError(errno.EIO, os.strerror(errno.EIO))


async def write_read_i2c(fd, write_buf, read_len):
    """
    Write-to then read-from the I2C slave at `fd`.

    Note: The Pi's I2C bus isn't the best, and it fails sometimes.
          See: http://www.advamation.com/knowhow/raspberrypi/rpi-i2c-bug.html
          Therefore you will want to incorporate integrity checks
          when you read/write to the I2C bus. See the next function
          in this module for how to do this.
    """
    async with LOCK:
        await _write_i2c(fd, write_buf)
        return await _read_i2c(fd, read_len)


async def write_read_i2c_with_integrity(fd, write_buf, read_len):
    """
    Same as `write_read_i2c` but uses integrity checks for
    both the outgoing and incoming buffers. See the `integrity`
    module for details on how this works.
    """
    read_len = integrity.read_len_with_integrity(read_len)
    write_buf = integrity.put_integrity(write_buf)
    async with LOCK:
        await _write_i2c(fd, write_buf)
        read_buf = await _read_i2c(fd, read_len)
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
        async def func_wrapper(*args, **kwargs):
            for _ in range(n-1):
                try:
                    return await func(*args, **kwargs)
                except OSError:
                    await asyncio.sleep(0.05)  # <-- allow the I2C bus to chill-out before we try again
            return await func(*args, **kwargs)

        return func_wrapper

    return decorator


async def i2c_poll_until(func, desired_return_value, timeout_ms):
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
            ret = await func()
            if ret == desired_return_value:
                return ret, (time.time() - start_time) * 1000
        except OSError:
            pass

        if (time.time() - start_time) * 1000 > timeout_ms:
            raise TimeoutError("{} did not return {} before {} milliseconds".format(func, desired_return_value, timeout_ms))

