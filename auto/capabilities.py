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
This module provides a list of hardware capabilities of the device,
and provides a way to acquire and release those capabilities.
"""


def list_caps():
    """
    Return a sorted list of the hardware capabilities of this device.
    Each capability is referenced by a string, as returned by
    this function. You can acquire an interface to a capability
    by passing the capability's string label to the function
    `acquire()`.
    """
    return sorted(_CAPABILITIES_MAP.keys())


def acquire(capability_name):
    """
    Return an interface to the capability labeled by `capability_name`.
    The interface object returned here should be disposed of
    (when you are done using it) by passing it to the function
    `release()`.
    """
    iface = _CAPABILITIES_MAP[capability_name]['acquire'](capability_name)
    iface._capability_name = capability_name
    return iface


def release(capability_iface):
    """
    Release the capability, freeing it's resources, etc.
    The `capability_iface` object must be one that was returned
    from `acquire()`.
    """
    capability_name = capability_iface._capability_name
    return _CAPABILITIES_MAP[capability_name]['release'](capability_iface)


# The capabilities map below holds all capabilities of the device.
# Names of capabilities are keys. The value of each is a dictionary
# with two callables -- one callable to acquire the capability's iface,
# and the other callable to release it.

_CAPABILITIES_MAP = {}


# The next section fills the _CAPABILITIES_MAP with the controller's
# capabilities.

from cio import rpc_client

for cio_capability in rpc_client.CAPS:
    _CAPABILITIES_MAP[cio_capability] = {
            'acquire': rpc_client.acquire_component_interface,
            'release': rpc_client.dispose_component_interface,
    }


# The next section puts the camera into the _CAPABILITIES_MAP
# This is convenient so that we can access the camera just like
# any other capability.

def _acquire_camera(_):
    from auto.camera import global_camera
    return global_camera()

def _release_camera(_):
    from auto.camera import close_global_camera
    close_global_camera()

_CAPABILITIES_MAP['Camera'] = {
        'acquire': _acquire_camera,
        'release': _release_camera,
}

