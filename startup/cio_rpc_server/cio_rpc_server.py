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
Expose the `cio` package through a single-threaded, multi-client RPC interface.
"""

# References:
# - http://www.gevent.org/intro.html
# - http://sdiehl.github.io/gevent-tutorial
# - https://dev.nextthought.com/blog/2018/05/gevent-hub.html
# - https://dev.nextthought.com/blog/2018/05/implementing-gevent-locks.html
# - https://dev.nextthought.com/blog/2018/06/gevent-blocking-greenlets.html
# - https://dev.nextthought.com/blog/2018/06/gevent-blocking-tracing.html

from gevent import monkey; monkey.patch_all()
from gevent.lock import Semaphore
import gevent
import rpyc
import types
import functools
from collections import defaultdict
import sys

from auto import logger
log = logger.init('cio_rpc_server', terminal=True)


from cio import default_handle as h


def _format_args(args, kwargs):
    args = ', '.join([repr(a) for a in args])
    kwargs = ', '.join(['{}={}'.format(k, repr(v)) for k, v in kwargs.items()])
    if args and kwargs:
        return args + ', ' + kwargs
    elif kwargs:
        return kwargs
    else:
        return args


class ComponentManager:

    def __init__(self, global_lock):
        self.lock = global_lock
        self.iface_lookup = {}   # map from name to iface
        self.name_lookup = {}    # map from iface to name
        self.counts = {}         # map from iface to set-of-connection-names
        self.callbacks = {}      # map from (iface, connection-name) to callback

    def _build_locked_method(self, method):
        lock = self.lock

        @functools.wraps(method)
        def locked_method(self, *args, **kwargs):
            with lock:
                log.info("calling {}.{}({})".format(
                    type(self).__name__, method.__name__, _format_args(args, kwargs)))
                ret = method(*args, **kwargs)
            return ret

        return locked_method

    def _lock_and_expose_methods(self, iface):
        public_method_names = set(attr for attr in dir(iface) if not attr.startswith('_'))
        for method_name in public_method_names:
            method = getattr(iface, method_name)
            locked_method = self._build_locked_method(method)
            exposed_method_name = 'exposed_{}'.format(method_name)
            setattr(iface, exposed_method_name, types.MethodType(locked_method, iface))
        return iface

    def acquire(self, conn_name, component_name, callback):
        # The lock is already held -- this method is only called by the ControllerService
        if component_name in self.iface_lookup:
            iface = self.iface_lookup[component_name]
            self.counts[iface].add(conn_name)
            log.info("{} acquired existing component {}".format(conn_name, component_name))
        else:
            iface = h.acquire_component_interface(component_name)
            iface = self._lock_and_expose_methods(iface)
            self.iface_lookup[component_name] = iface
            self.name_lookup[iface] = component_name
            self.counts[iface] = {conn_name}
            log.info("{} acquired first-time component {}".format(conn_name, component_name))
        if callback is not None:
            self.callbacks[(iface, conn_name)] = callback
        return iface

    def dispose(self, conn_name, iface):
        # The lock is already held -- this method is only called by the ControllerService
        assert iface in self.name_lookup
        component_name = self.name_lookup[iface]
        self.counts[iface].remove(conn_name)
        if len(self.counts[iface]) == 0:
            del self.iface_lookup[component_name]
            del self.name_lookup[iface]
            del self.counts[iface]
            h.dispose_component_interface(iface)
            log.info("{} disposed first-time component {}".format(conn_name, component_name))
        else:
            log.info("{} disposed existing component {}".format(conn_name, component_name))
        if (iface, conn_name) in self.callbacks:
            del self.callbacks[(iface, conn_name)]

    def callback_thread(self):
        #######
        # THIS DOES NOT WORK PROPERLY -- NEEDS SOME MAJOR STUDY
        #
        # It sorta works... but there are two problems.
        #  1. It is slow. It delivers callbacks like 10x too slowly.
        #  2. It causes everything to freeze if the client disconnects
        #     abruptly. The whole gevent loops gets hung... :(
        #
        # For now, just don't use this callback feature and everything
        # works great.
        #######
        while True:
            ifaces = set(iface for (iface, _), _ in self.callbacks.items())

            with self.lock:
                iface_to_value = {}
                for iface in ifaces:
                    val = iface()
                    iface_to_value[iface] = val

            needs_call = []
            for (iface, conn_name), callback in self.callbacks.items():
                # We don't do any IO in this loop because we're using shared memory so we don't want to yeild here.
                val = iface_to_value[iface]
                needs_call.append((callback, val, conn_name))

            for callback, val, conn_name in needs_call:
                callback(val)
                log.info("Invoked callback for iface ({}) on connection ({}) ==> {}"
                        .format(type(iface).__name__, conn_name, val))

            if len(needs_call) == 0:  # <-- i.e. "if we didn't do any IO above"
                gevent.sleep(0.01)


class ControllerService(rpyc.Service):

    def __init__(self, component_manager, global_lock):
        self.cm = component_manager
        self.lock = global_lock
        self.is_redirecting_stdio = False

    def on_connect(self, conn):
        with self.lock:
            self.conn = conn
            self.conn_name = self.conn._config["connid"]
            self.active_ifaces = set()   # set of active component interfaces
            log.info("New client: {}".format(self.conn_name))

    def on_disconnect(self, conn):
        with self.lock:
            for iface in self.active_ifaces:
                self.cm.dispose(self.conn_name, iface)
            self.active_ifaces = set()
            log.info("Dead client: {}".format(self.conn_name))
            if self.is_redirecting_stdio:
                self._restore_stdio()

    def exposed_capabilities(self):
        with self.lock:
            return tuple(sorted(h.CAPS.keys()))

    def exposed_acquire_component_interface(self, component_name, callback=None):
        with self.lock:
            iface = self.cm.acquire(self.conn_name, component_name, callback)
            self.active_ifaces.add(iface)
            return iface

    def exposed_dispose_component_interface(self, iface):
        with self.lock:
            self.cm.dispose(self.conn_name, iface)
            self.active_ifaces.remove(iface)

    def exposed_redirect_stdio(self, stdin=None, stdout=None, stderr=None):
        with self.lock:
            if stdin  is not None:  sys.stdin  = stdin
            if stdout is not None:  sys.stdout = stdout
            if stderr is not None:  sys.stderr = stderr
            self.is_redirecting_stdio = True

    def exposed_restore_stdio(self):
        with self.lock:
            self._restore_stdio()

    def _restore_stdio(self):
        # The lock is already held when this method is called.
        sys.stdin  = sys.__stdin__
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        self.is_redirecting_stdio = False


if __name__ == "__main__":

    from rpyc.utils.server import GeventServer
    from rpyc.utils.helpers import classpartial

    global_lock = Semaphore(value=1)

    component_manager = ComponentManager(global_lock)

    ControllerService = classpartial(ControllerService, component_manager, global_lock)

    rpc_server = GeventServer(ControllerService, port=18861)

    log.info("RUNNING!")

    gevent.joinall([
        gevent.spawn(rpc_server.start),
        #gevent.spawn(component_manager.callback_thread),
    ])

