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
def soft_reset(fd):
    """
    Instruct the controller's capabilities module to do a soft-reset.
    This means that the list of enabled components will be reverted to
    the default list of enabled components and the list of available
    components will be repopulated.
    """
    write_read_i2c_with_integrity(fd, [CAPABILITIES_REG_NUM, 0x00], 0)


@i2c_retry(N_I2C_TRIES)
def is_ready(fd):
    """
    Check to see if the controller is ready for normal operation. This
    is important to do on startup and after a hard- or soft-reset. It's
    even better to poll this function to wait for the controller to be
    ready, i.e.
      |  soft_reset(fd)
      |  i2c_poll_until(lambda: is_ready(fd), True, timeout_ms=1000)
    """
    ready, = write_read_i2c_with_integrity(fd, [CAPABILITIES_REG_NUM, 0x01], 1)
    return ready == 1


@i2c_retry(N_I2C_TRIES)
def get_num_components(fd, only_enabled):
    """
    Retrieve the number of components in either the list of available components
    (when `only_enabled=False`) or the list of enabled components (when `only_enabled=True`).
    """
    which_list = 0x01 if only_enabled else 0x00
    lsb, msb = write_read_i2c_with_integrity(fd, [CAPABILITIES_REG_NUM, 0x02, which_list], 2)
    return (msb << 8) | lsb


@i2c_retry(N_I2C_TRIES)
def get_list_of_components(fd, n_components, only_enabled):
    """
    Retrieve either the list of available components (when `only_enabled=False`)
    or the list of enabled components (when `only_enabled=True`). This returns a
    list of components' register numbers. You must pass `n_components` to this
    function so that it know how many components are in the list (you should
    call `get_num_components` to obtain `n_components`).
    """
    which_list = 0x01 if only_enabled else 0x00
    buf = write_read_i2c_with_integrity(fd, [CAPABILITIES_REG_NUM, 0x03, which_list], n_components)
    return list(buf)


@i2c_retry(N_I2C_TRIES)
def get_component_name(fd, register_number):
    """
    Retrieve the component name whose register number is `register_number`.
    """
    buf = write_read_i2c_with_integrity(fd, [CAPABILITIES_REG_NUM, 0x04, register_number], MAX_COMPONENT_NAME_LEN)
    return buf.replace(b'\x00', b'').decode('utf8')


@i2c_retry(N_I2C_TRIES)
def enable_component(fd, register_number):
    """
    Enable the controller's component whose register number is `register_number`.
    Return a string representing the state of the component, or raise an exception
    on error.
    Note: After you enable a component, you should wait for the controller to loop_once
          so that you can reliably query that component and receive up-to-date info.
          As such, poll `is_ready` until it return True after you enable a component. I.e.
              |  enable_component(fd, ...)
              |  i2c_poll_until(lambda: is_ready(fd), True, timeout_ms=1000)
    """
    indicator, = write_read_i2c_with_integrity(fd, [CAPABILITIES_REG_NUM, 0x05, register_number], 1)
    if indicator == 0: return "already enabled"
    if indicator == 1: return "now enabled"
    if indicator == 2: raise Exception("invalid register address!")
    raise Exception("unknown return value: {}".format(indicator))


@i2c_retry(N_I2C_TRIES)
def disable_component(fd, register_number):
    """
    Disable the controller's component whose register number is `register_number`.
    Return a string representing the state of the component, or raise an exception
    on error.
    """
    indicator, = write_read_i2c_with_integrity(fd, [CAPABILITIES_REG_NUM, 0x06, register_number], 1)
    if indicator == 0: return "already disabled"
    if indicator == 1: return "now disabled"
    if indicator == 2: raise Exception("invalid register address!")
    raise Exception("unknown return value: {}".format(indicator))


@i2c_retry(N_I2C_TRIES)
def is_component_enabled(fd, register_number):
    """
    Return True if the component is currently enabled, False if the component
    is not currently enabled, or raise an exception if the component doesn't
    exist.
    """
    indicator, = write_read_i2c_with_integrity(fd, [CAPABILITIES_REG_NUM, 0x07, register_number], 1)
    if indicator == 0: return False
    if indicator == 1: return True
    if indicator == 2: raise Exception("invalid register address!")
    raise Exception("unknown return value: {}".format(indicator))


def get_capabilities(fd, soft_reset_first=False, only_enabled=False, detect_enabledness=False):
    """
    Return a dictionary representing the capabilities of the connected controller.
    """
    if soft_reset_first:
        soft_reset(fd)
        i2c_poll_until(lambda: is_ready(fd), True, timeout_ms=1000)

    n_components     = get_num_components(fd, only_enabled)
    register_numbers = get_list_of_components(fd, n_components, only_enabled)

    caps = {}

    for reg in register_numbers:
        name = get_component_name(fd, reg)
        if name != "Capabilities":
            caps[name] = {
                    'register_number': reg,
            }
            if detect_enabledness:
                caps[name]['is_enabled'] = is_component_enabled(fd, reg)

    return caps


def acquire_component_interface(fd, caps, component_name):
    """
    Acquire the interface to the component having the name `component_name`.
    This is a helper function which will:
        1. Enable the component.
        2. Wait for the controller to be ready.
        3. Lookup, build, and return the interface object for the component.
    Note, when you are finished using the components interface, you should
    call `dispose_component_interface`.
    """
    register_number = caps[component_name]['register_number']
    interface = KNOWN_COMPONENTS[component_name](fd, register_number)
    enable_component(fd, register_number)
    i2c_poll_until(lambda: is_ready(fd), True, timeout_ms=1000)
    interface.__fd__ = fd
    interface.__reg__ = register_number
    return interface


def dispose_component_interface(interface):
    """
    Dispose the component `interface` by disabling the underlying component.
    This function only works for interfaces returned by `acquire_component_interface`.
    """
    fd = interface.__fd__
    register_number = interface.__reg__
    disable_component(fd, register_number)
    i2c_poll_until(lambda: is_ready(fd), True, timeout_ms=1000)


def test_all(fd):
    caps = get_capabilities(fd)
    components = sorted(caps.keys())
    print("Components:", components)

    interfaces = [(name, acquire_component_interface(fd, caps, name)) for name in components]

    for name, interface in interfaces:
        print("{}: {}".format(name, interface))

    for name, interface in interfaces:
        dispose_component_interface(interface)

