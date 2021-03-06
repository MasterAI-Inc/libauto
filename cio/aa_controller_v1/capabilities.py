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
    if indicator == 0: indicator = "already enabled"
    elif indicator == 1: indicator = "now enabled"
    elif indicator == 0xFF: raise Exception("invalid register address!")
    else: raise Exception("unknown return value: {}".format(indicator))
    log.info('Enabled component register number {}; status is: {}'.format(register_number, indicator))
    return indicator


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
    if indicator == 0: indicator = "already disabled"
    elif indicator == 1: indicator = "now disabled"
    elif indicator == 0xFF: raise Exception("invalid register address!")
    else: raise Exception("unknown return value: {}".format(indicator))
    log.info('Disabled component register number {}; status is: {}'.format(register_number, indicator))
    return indicator


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


async def get_capabilities(fd, soft_reset_first=False, only_enabled=False):
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
        if name == 'BatteryVoltageReader': name = 'Power'
        if name != "Capabilities":
            caps[name] = {
                    'register_number': reg,
            }
            caps[name]['is_enabled'] = (await get_component_status(fd, reg) == 'ENABLED')

    if 'Timer1PWM' in caps and 'Timer3PWM' in caps:
        # Bodge.
        t1_reg_num = caps['Timer1PWM']['register_number']
        t3_reg_num = caps['Timer3PWM']['register_number']
        is_enabled = caps['Timer3PWM']['is_enabled']
        caps['PWMs'] = {'register_number': (t1_reg_num, t3_reg_num), 'is_enabled': is_enabled}
        del caps['Timer1PWM']
        del caps['Timer3PWM']

    caps['Credentials'] = {
            'register_number': None,  # <-- this is a virtual component; it is implemented on the Python side, not the controller side
            'is_enabled': False
    }

    return caps


async def acquire_component_interface(fd, caps, ref_count, component_name):
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

    if component_name not in ref_count:
        # It must not be enabled and the ref count must currently be zero.
        ref_count[component_name] = 1

    else:
        # The component is already enabled, we just need to inc the ref count.
        ref_count[component_name] += 1

    # ALWAYS ENABLE THE COMPONENT AND WAIT FOR IT.
    # We must have a bug in the controller code... because for some reason
    # we have to enable the components which are already enabled by default.
    # My best guess is that we need to add a few `volatile` keywords... that
    # is, my best guess is that the `status` of the component in the controller
    # is being held in a register (or some cache line). The behavior I'm seeing
    # is that the `if` condition in the link below is not evaluating to `true`
    # (even though it should!) ... thus my theory about the caching of the
    # `status`. It's still a wild guess, really, so who knows.
    #   https://github.com/MasterAI-Inc/autoauto-controller/blob/0c234f3e8abfdc34a5011481e140998560097cbc/libraries/aa_controller/Capabilities.cpp#L526
    # Anyway, if that bug were fixed, then the whole next bock would be moved
    # such that it would only run `if component_name not in ref_count` above.
    orig_register_number = register_number
    if not isinstance(register_number, (tuple, list)):
        register_number = [register_number]
    for n in register_number:
        if n is None:
            continue
        await enable_component(fd, n)
        async def _get_component_status():
            return await get_component_status(fd, n)
        await i2c_poll_until(_get_component_status, 'ENABLED', timeout_ms=1000)

    log.info('Acquired {}, register number {}, now having ref count {}.'.format(component_name, orig_register_number, ref_count[component_name]))

    return interface


async def release_component_interface(ref_count, interface):
    """
    Release the component `interface` by disabling the underlying component.
    This function only works for interfaces returned by `acquire_component_interface`.
    """
    fd = interface.__fd__
    register_number = interface.__reg__
    component_name = interface.__component_name__

    orig_register_number = register_number

    if component_name not in ref_count:
        # Weird... just bail.
        return

    # Dec the ref count.
    ref_count[component_name] -= 1
    ref_count_here = ref_count[component_name]

    if ref_count[component_name] == 0:
        # This is the last remaining reference, so we'll disable the component.
        if not isinstance(register_number, (tuple, list)):
            register_number = [register_number]
        for n in register_number:
            if n is None:
                continue
            await disable_component(fd, n)
            async def _get_component_status():
                return await get_component_status(fd, n)
            await i2c_poll_until(_get_component_status, 'DISABLED', timeout_ms=1000)
        del ref_count[component_name]

    log.info('Released {}, register number {}, now having ref count {}.'.format(component_name, orig_register_number, ref_count_here))

