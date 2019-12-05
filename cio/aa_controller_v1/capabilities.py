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
                      i2c_retry,
                      i2c_poll_until)
from . import N_I2C_TRIES
from .components import KNOWN_COMPONENTS


CAPABILITIES_REG_NUM = 0x01
MAX_COMPONENT_NAME_LEN = 25


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
async def get_num_components(fd, only_enabled):
    """
    Retrieve the number of components in either the list of available components
    (when `only_enabled=False`) or the list of enabled components (when `only_enabled=True`).
    """
    which_list = 0x01 if only_enabled else 0x00
    lsb, msb = await write_read_i2c_with_integrity(fd, [CAPABILITIES_REG_NUM, 0x02, which_list], 2)
    return (msb << 8) | lsb


@i2c_retry(N_I2C_TRIES)
async def get_list_of_components(fd, n_components, only_enabled):
    """
    Retrieve either the list of available components (when `only_enabled=False`)
    or the list of enabled components (when `only_enabled=True`). This returns a
    list of components' register numbers. You must pass `n_components` to this
    function so that it know how many components are in the list (you should
    call `get_num_components` to obtain `n_components`).
    """
    which_list = 0x01 if only_enabled else 0x00
    buf = await write_read_i2c_with_integrity(fd, [CAPABILITIES_REG_NUM, 0x03, which_list], n_components)
    return list(buf)


@i2c_retry(N_I2C_TRIES)
async def get_component_name(fd, register_number):
    """
    Retrieve the component name whose register number is `register_number`.
    """
    buf = await write_read_i2c_with_integrity(fd, [CAPABILITIES_REG_NUM, 0x04, register_number], MAX_COMPONENT_NAME_LEN)
    return buf.replace(b'\x00', b'').decode('utf8')


@i2c_retry(N_I2C_TRIES)
async def enable_component(fd, register_number):
    """
    Enable the controller's component whose register number is `register_number`.
    Return a string representing the state of the component, or raise an exception
    on error.
    Note: After you enable a component, you should wait for the controller to tell you
          that it has _actually_ been enabled before you try to communicate with it.
          See how it is done in `acquire_component_interface()`.
    """
    indicator, = await write_read_i2c_with_integrity(fd, [CAPABILITIES_REG_NUM, 0x05, register_number], 1)
    if indicator == 0: return "already enabled"
    if indicator == 1: return "now enabled"
    if indicator == 0xFF: raise Exception("invalid register address!")
    raise Exception("unknown return value: {}".format(indicator))


@i2c_retry(N_I2C_TRIES)
async def disable_component(fd, register_number):
    """
    Disable the controller's component whose register number is `register_number`.
    Return a string representing the state of the component, or raise an exception
    on error.
    Note: After you disable a component, you should wait for the controller to tell
          you that it has _actually_ been disabled. See how it is done in
          `release_component_interface()`.
    """
    indicator, = await write_read_i2c_with_integrity(fd, [CAPABILITIES_REG_NUM, 0x06, register_number], 1)
    if indicator == 0: return "already disabled"
    if indicator == 1: return "now disabled"
    if indicator == 0xFF: raise Exception("invalid register address!")
    raise Exception("unknown return value: {}".format(indicator))


@i2c_retry(N_I2C_TRIES)
async def get_component_status(fd, register_number):
    """
    Return a string representing the component's status. It will be one of:
     - ENABLE_PENDING
     - ENABLED
     - DISABLE_PENDING
     - DISABLED
    Or raise an error.
    """
    indicator, = await write_read_i2c_with_integrity(fd, [CAPABILITIES_REG_NUM, 0x07, register_number], 1)
    if indicator == 0: return 'DISABLED'
    if indicator == 1: return 'ENABLE_PENDING'
    if indicator == 2: return 'ENABLED'
    if indicator == 3: return 'DISABLE_PENDING'
    raise Exception("unknown return value: {}".format(indicator))


async def get_capabilities(fd, soft_reset_first=False, only_enabled=False, detect_enabledness=False):
    """
    Return a dictionary representing the capabilities of the connected controller.
    """
    if soft_reset_first:
        await soft_reset(fd)
        async def _is_ready():
            return await is_ready(fd)
        await i2c_poll_until(_is_ready, True, timeout_ms=1000)

    n_components     = await get_num_components(fd, only_enabled)
    register_numbers = await get_list_of_components(fd, n_components, only_enabled)

    caps = {}

    for reg in register_numbers:
        name = await get_component_name(fd, reg)
        if name != "Capabilities":
            caps[name] = {
                    'register_number': reg,
            }
            if detect_enabledness:
                caps[name]['is_enabled'] = (await get_component_status(fd, reg) == 'ENABLED')

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
    await enable_component(fd, register_number)
    async def _get_component_status():
        return await get_component_status(fd, register_number)
    await i2c_poll_until(_get_component_status, 'ENABLED', timeout_ms=1000)
    interface.__fd__ = fd
    interface.__reg__ = register_number
    return interface


async def release_component_interface(interface):
    """
    Release the component `interface` by disabling the underlying component.
    This function only works for interfaces returned by `acquire_component_interface`.
    """
    fd = interface.__fd__
    register_number = interface.__reg__
    await disable_component(fd, register_number)
    async def _get_component_status():
        return await get_component_status(fd, register_number)
    await i2c_poll_until(_get_component_status, 'DISABLED', timeout_ms=1000)

