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
"""

import asyncio
import auto
from threading import Thread


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
        thread = Thread(target=_loop_main, args=(_BG_LOOP,))
        thread.daemon = True  # <-- thread will exit when main thread exists
        thread.start()
        if verbose:
            auto.print_all("Instantiated an event loop in a background thread!")
        return _BG_LOOP


def _loop_main(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

