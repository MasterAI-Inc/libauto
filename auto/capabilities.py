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
This module provides a list of hardware capabilities of the device,
and provides a way to acquire and release those capabilities.

This module provides a fully **synchronous** interface.
"""

from auto.asyncio_tools import get_loop
from auto.services.controller.client_sync import CioRoot


def list_caps():
    """
    Return a sorted tuple of the hardware capabilities of this device.
    Each capability is referenced by a string, as returned by
    this function. You can acquire an interface to a capability
    by passing the capability's string label to the function
    `acquire()`.
    """
    global _CAPABILITIES_MAP

    try:
        return tuple(sorted(_CAPABILITIES_MAP.keys()))

    except NameError:
        pass  # We can remedy this.

    loop = get_loop()

    controller_connection = CioRoot(loop)

    _CAPABILITIES_MAP = {}

    for capability_id in controller_connection.init():
        _CAPABILITIES_MAP[capability_id] = {
                'acquire': controller_connection.acquire,
                'release': controller_connection.release,
        }

    return tuple(sorted(_CAPABILITIES_MAP.keys()))


def acquire(capability_name):
    """
    Return an interface to the capability labeled by `capability_name`.
    Call `list_caps()` to obtain a list of supported capabilities.
    The interface object returned here should be disposed of
    (when you are done using it) by passing it to the function
    `release()`.
    """
    if capability_name not in list_caps():
        raise AttributeError("The given capability name (\"{}\") is not available.".format(capability_name))
    iface = _CAPABILITIES_MAP[capability_name]['acquire'](capability_name)
    iface._capability_name = capability_name
    return iface


def release(capability_iface):
    """
    Release the capability, freeing it's resources, etc.
    The `capability_iface` object must be one that was returned
    from `acquire()`.
    """
    capability_name = getattr(capability_iface, "_capability_name", None)
    if capability_name is None:
        raise Exception("The object passed as `capability_iface` was not acquired by `acquire()`; you must pass the exact object obtained from `acquire()`.")
    if capability_name not in list_caps():
        raise Exception("The given capability name (\"{}\") is not available.".format(capability_name))
    return _CAPABILITIES_MAP[capability_name]['release'](capability_iface)

