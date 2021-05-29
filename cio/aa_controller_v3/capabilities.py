###############################################################################
#
# Copyright (c) 2017-2020 Master AI, Inc.
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from Master AI, Inc.
#
###############################################################################

from .easyi2c import (write_read_i2c_with_integrity,
                      i2c_retry,
                      i2c_poll_until)
from . import N_I2C_TRIES

from auto import logger
log = logger.init(__name__, terminal=True)

import struct


CAPABILITIES_REG_NUM = 0x01


# We hard-code the capabilities of this controller.
CAPABILITIES_LIST = [
    (0, 'VersionInfo'),
    (1, 'Capabilities'),
    (2, 'LEDs'),
    (3, 'ADC'),
    (3, 'Photoresistor'),
    (4, 'CarMotors'),
    (None, 'Credentials'),
    (None, 'Calibrator'),
    (None, 'Camera'),
]


@i2c_retry(N_I2C_TRIES)
async def soft_reset(fd):
    """
    Instruct the controller's capabilities module to do a soft-reset.
    """
    await write_read_i2c_with_integrity(fd, [CAPABILITIES_REG_NUM, 0x00], 0)


@i2c_retry(N_I2C_TRIES)
async def is_ready(fd):
    """
    Check to see if the controller is ready for normal operation. This
    is important to do on startup and after a hard- or soft-reset. It's
    even better to poll this function to wait for the controller to be
    ready, i.e.
      |  await soft_reset(fd)
      |
      |  async def _is_ready():
      |      return await is_ready(fd)
      |
      |  await i2c_poll_until(_is_ready, True, timeout_ms=1000)
    """
    ready, = await write_read_i2c_with_integrity(fd, [CAPABILITIES_REG_NUM, 0x01], 1)
    return ready == 1


@i2c_retry(N_I2C_TRIES)
async def _eeprom_store(fd, addr, buf):
    if not isinstance(buf, bytes):
        raise Exception('`buf` should be `bytes`')
    if len(buf) > 4:
        raise Exception('you may only store 4 bytes at a time')
    if addr < 0 or addr + len(buf) > 1024:
        raise Exception('invalid `addr`: EEPROM size is 1024 bytes')
    payload = list(struct.pack('1H', addr)) + [len(buf)] + list(buf)
    await write_read_i2c_with_integrity(fd, [CAPABILITIES_REG_NUM, 0x08] + payload, 0)


@i2c_retry(N_I2C_TRIES)
async def _is_eeprom_store_finished(fd):
    status, = await write_read_i2c_with_integrity(fd, [CAPABILITIES_REG_NUM, 0x09], 1)
    return status == 0


@i2c_retry(N_I2C_TRIES)
async def _eeprom_query(fd, addr, length):
    if length > 4:
        raise Exception('you may only retrieve 4 bytes at a time')
    if addr < 0 or addr + length > 1024:
        raise Exception('invalid `addr`: EEPROM size is 1024 bytes')
    payload = list(struct.pack('1H', addr)) + [length]
    await write_read_i2c_with_integrity(fd, [CAPABILITIES_REG_NUM, 0x0A] + payload, 0)


@i2c_retry(N_I2C_TRIES)
async def _is_eeprom_query_finished(fd):
    status, = await write_read_i2c_with_integrity(fd, [CAPABILITIES_REG_NUM, 0x0B], 1)
    return status == 0


@i2c_retry(N_I2C_TRIES)
async def _retrieve_eeprom_query_buf(fd, length):
    buf = await write_read_i2c_with_integrity(fd, [CAPABILITIES_REG_NUM, 0x0C], length)
    return buf


async def eeprom_store(fd, addr, buf):
    for i in range(0, len(buf), 4):
        buf_here = buf[i:i+4]
        await _eeprom_store(fd, addr + i, buf_here)
        async def is_eeprom_store_finished():
            return await _is_eeprom_store_finished(fd)
        await i2c_poll_until(is_eeprom_store_finished, True, timeout_ms=1000)


async def eeprom_query(fd, addr, length):
    bufs = []
    i = 0
    while length > 0:
        length_here = min(length, 4)
        await _eeprom_query(fd, addr + i, length_here)
        async def is_eeprom_query_finished():
            return await _is_eeprom_query_finished(fd)
        await i2c_poll_until(is_eeprom_query_finished, True, timeout_ms=1000)
        buf_here = await _retrieve_eeprom_query_buf(fd, length_here)
        bufs.append(buf_here)
        length -= length_here
        i += length_here
    return b''.join(bufs)


async def get_capabilities(fd, soft_reset_first=False, only_enabled=False):
    """
    Return a dictionary representing the capabilities of the connected controller.
    """
    if soft_reset_first:
        await soft_reset(fd)
        async def _is_ready():
            return await is_ready(fd)
        await i2c_poll_until(_is_ready, True, timeout_ms=1000)

    caps = {}

    for reg, name in CAPABILITIES_LIST:
        if name != "Capabilities":
            caps[name] = {
                'fd': fd,
                'register_number': reg,
            }

    return caps

