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
CAPS = set(CONN.root.capabilities())


def acquire_component_interface(component_name):
    """
    Enable and acquire the component with the given name.
    """
    return CONN.root.acquire_component_interface(component_name)


def dispose_component_interface(interface):
    """
    Dispose of this component. If there are no other references
    to this component interfaces, then the component will also be
    disabled.
    """
    return CONN.root.dispose_component_interface(interface)


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

