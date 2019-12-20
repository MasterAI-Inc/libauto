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
This module can launch a Python asyncio event loop in a background thread.
You create and get the event loop by calling `get_loop()`. It is a singleton;
the same loop is returned on every invocation, and it is not created until the
first invocation.

The purpose of this background-thread event loop is so that the main thread
can run **synchronous** code (as feels natural for beginner programmers), but
we can still reap the power of the asyncio event loop through delegation to
the background loop. When students advance enough, we can teach them how to
ditch this background loop and how to use a main-thread async loop to write
a fully asynchronous (cooperative) program! Indeed, the libauto library is
async under-the-hood.

This module also provides a function to wrap an async interface into a
synchronous one, delegating to the underlying loop to invoke the wrapped
async methods. See `wrap_async_to_sync()`.
"""

import asyncio
import inspect
from threading import Thread

import auto
from auto.rpc.serialize_interface import serialize_interface
from auto.rpc.build_interface import build_interface


DEBUG_ASYNCIO = False


def get_loop(verbose=False):
    """
    Obtain the Python asyncio event loop which is running in a background thread.
    The loop (and its background thread) are not created until you invoke this
    function for the first time. The same loop is returned on all subsequent calls.
    """
    global _BG_LOOP
    try:
        return _BG_LOOP
    except NameError:
        _BG_LOOP = asyncio.new_event_loop()
        _set_async_debug_and_log_level(_BG_LOOP)
        thread = Thread(target=_loop_main, args=(_BG_LOOP,))
        thread.daemon = True  # <-- thread will exit when main thread exists
        thread.start()
        _setup_cleanup(_BG_LOOP, thread)
        if verbose:
            auto.print_all("Instantiated an event loop in a background thread!")
        return _BG_LOOP


def _loop_main(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


def _set_async_debug_and_log_level(loop):
    # Do you want debugging turned on?
    if DEBUG_ASYNCIO:
        loop.set_debug(True)   # It's off by default, so we turn it on when we want it.

    # Btw, we could also change the log level. For more info, see:
    #   https://docs.python.org/3.7/library/asyncio-dev.html#asyncio-logger
    #
    # E.g. We could do:
    #   import logging
    #   logging.getLogger("asyncio").setLevel(logging.WARNING)
    #
    # But I don't think we need it...


def _setup_cleanup(loop, thread):
    """
    Attempt to cleanup the event loop and the background thread _properly_.
    This cleanup is only done when DEBUG_ASYNCIO is True; else, we just
    let the asyncio thread die quickly and painlessly, without giving it a
    chance to close or print warnings.
    """
    if not DEBUG_ASYNCIO:
        return

    def cleanup():
        async def _stop_loop():
            loop.stop()

        asyncio.run_coroutine_threadsafe(_stop_loop(), loop)
        thread.join()
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()

    import atexit
    atexit.register(cleanup)


def wrap_async_to_sync(obj, loop=None):
    """
    Build and return an object which wraps `obj`, turning each of `obj`'s async
    methods into "normal" synchronous methods.

    **Note:** Only _methods_ are wrapped, so if `obj` has _attributes_ which it
              exposes, those will _not_ be accessible through the wrapped object.
              This is a known limitation which will not be addressed (it is
              too complex to expose wrapped attributes in such a way that
              preserves their mutability or lack thereof; thus only methods
              will be exposed by the wrapper). Also, magic methods are _not_
              wrapped; this is a limitation we may fix in the future.
    """
    if loop is None:
        loop = get_loop()

    typename = type(obj).__name__
    typemodule = type(obj).__module__
    typedoc = inspect.getdoc(type(obj))

    TheDynamicType = type(typename, (object,), {})
    TheDynamicType.__module__ = typemodule
    TheDynamicType.__doc__ = typedoc

    instance = TheDynamicType()

    for attr_name in dir(obj):
        if attr_name.startswith('__'):
            # We won't try to fix magic methods (too much craziness to try that).
            continue

        attr = getattr(obj, attr_name)

        if not inspect.isfunction(attr) and not inspect.ismethod(attr):
            # We only care about functions and methods.
            continue

        iface, _ = serialize_interface(attr, attr_name)

        if not iface['is_async']:
            # This is a normal synchronous function or method, so we just copy it over.
            setattr(instance, attr_name, attr)

        else:
            # This is an asynchronous function or method, so we need to do some shenanigans
            # to turn it into a normal synchronous function or method.
            iface['is_async'] = False

            impl_transport = _closure_build_impl_transport(attr, loop)  # <-- Need to close over `attr` to freeze it, since it is reassigned in the loop above.

            if iface['ismethod']:
                sub_name, sub_attr = build_interface(iface, impl_transport, is_method=True)
                assert attr_name == sub_name
                setattr(TheDynamicType, sub_name, sub_attr)
            else:
                sub_name, sub_attr = build_interface(iface, impl_transport, is_method=False)
                assert attr_name == sub_name
                setattr(instance, sub_name, sub_attr)

    return instance


def _closure_build_impl_transport(attr, loop):
    def impl_transport(path, args):
        coro = attr(*args)
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result()

    return impl_transport

