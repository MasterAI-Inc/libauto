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
from .components import KNOWN_COMPONENTS

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
]


@i2c_retry(N_I2C_TRIES)
async def soft_reset(fd):
    """
    Instruct the controller's capabilities module to do a soft-reset.
    This means that the list of enabled components will be reverted to
    the default list of enabled components and the list of available
    components will be repopulated.
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
    await _eeprom_store(fd, addr, buf)
    async def is_eeprom_store_finished():
        return await _is_eeprom_store_finished(fd)
    await i2c_poll_until(is_eeprom_store_finished, True, timeout_ms=1000)


async def eeprom_query(fd, addr, length):
    await _eeprom_query(fd, addr, length)
    async def is_eeprom_query_finished():
        return await _is_eeprom_query_finished(fd)
    await i2c_poll_until(is_eeprom_query_finished, True, timeout_ms=1000)
    return await _retrieve_eeprom_query_buf(fd, length)


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
                    'register_number': reg,
            }
            caps[name]['is_enabled'] = True

    for c in ['Credentials', 'Calibrator']:
        caps[c] = {
                'register_number': None,  # <-- this is a virtual component; it is implemented on the Python side, not the controller side
                'is_enabled': False
        }

    return caps


async def acquire_component_interface(fd, caps, component_name):
    """
    Acquire the interface to the component having the name `component_name`.
    This is a helper function which will:
        1. Enable the component.
        2. Wait for the controller to be ready.
        3. Lookup, build, and return the interface object for the component.
    Note, when you are finished using the components interface, you should
    call `release_component_interface`.
    """
    register_number = caps[component_name]['register_number']
    interface = KNOWN_COMPONENTS[component_name](fd, register_number)
    interface.__fd__ = fd
    interface.__reg__ = register_number
    interface.__component_name__ = component_name
    return interface


async def release_component_interface(interface):
    """
    Release the component `interface` by disabling the underlying component.
    This function only works for interfaces returned by `acquire_component_interface`.
    """
    fd = interface.__fd__
    register_number = interface.__reg__
    component_name = interface.__component_name__

    # Nothing to do here, since we don't disable components in this controller and we don't do ref counting...

