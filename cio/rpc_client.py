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
Connect to the cio RPC server, and offer up and interface that _feels_ like
there is no RPC. You can write code as if you are using the cio interface
directly!

For the server, see `startup/cio_rpc_server/cio_rpc_server.py`.
"""

import rpyc
CONN = rpyc.connect("localhost", 18861, config={'sync_request_timeout': 300})
#bgsrv = rpyc.BgServingThread(CONN)


"""
The capabilities of the controller.
"""
VERSION = CONN.root.version()
CAPS = set(CONN.root.capabilities())


def acquire_component_interface(component_name):
    """
    Enable and acquire the component with the given name.
    """
    remote_iface = CONN.root.acquire_component_interface(component_name)
    interface = RemoteInterfaceWrapper(remote_iface)
    return interface


def dispose_component_interface(interface):
    """
    Dispose of this component. If there are no other references
    to this component interfaces, then the component will also be
    disabled.
    """
    remote_iface = interface._remote_iface
    return CONN.root.dispose_component_interface(remote_iface)


def redirect_stdio(stdin=None, stdout=None, stderr=None):
    """
    Redirect the remote stdio to wherever you want! The most
    common place to redirect the remote stdio is to our local
    stdio. E.g. `redirect_stdio(stdout=sys.stdout)`
    """
    if stdin is not None:
        stdin = rpyc.restricted(stdin, {'read'})
    if stdout is not None:
        stdout = rpyc.restricted(stdout, {'write', 'flush'})
    if stderr is not None:
        stderr = rpyc.restricted(stderr, {'write', 'flush'})
    CONN.root.redirect_stdio(stdin=stdin, stdout=stdout, stderr=stderr)


def restore_stdio():
    """
    Restore the remote stdio to its original state.
    """
    CONN.root.restore_stdio()


class RemoteInterfaceWrapper:
    """
    When you are dealing with a `netref` from `rpyc.core.netref`,
    you cannot set local attributes. Everything you do to that `netref`
    will be forwarded to the remote side (even creating new instance
    attributes will be forwarded to the other side). I want to be able to
    set local variables on my local object, and only have the things that
    don't exist locally to be forwarded to the remote side. This class
    gives me that behavior. You just pass your netref to this class
    as the `remote_iface`, and this class wraps it so that you can
    set local instance variables on objects of this class, but if
    you access a variable that doesn't exist, it will give you a
    remote reference to what you want.
    """

    def __init__(self, remote_iface):
        self._remote_iface = remote_iface

    def __getattr__(self, attr):
        return getattr(self._remote_iface, attr)

    def __str__(self):
        return self._remote_iface.__str__()

    def __repr__(self):
        return self._remote_iface.__repr__()

