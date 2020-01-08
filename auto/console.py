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
Module to interface with your AutoAuto device's front-panel console via RPC.

This is a **synchronous** interface.
"""

from auto.asyncio_tools import get_loop
from auto.services.console.client_sync import CuiRoot

_built_in_print = print


def _get_console():
    global _CONSOLE
    try:
        return _CONSOLE
    except:
        pass   # we can fix this

    loop = get_loop()
    _CONSOLE = CuiRoot(loop)
    _CONSOLE.init()
    return _CONSOLE


def print(*objects, sep=' ', end='\n'):
    """
    Print to the AutoAuto console! This function works the same
    as the build-in `print()` function in Python, but it prints
    to the AutoAuto console instead of to `stdout`.
    """
    all_text = []
    class Writable:
        def write(self, text):
            all_text.append(text)
        def flush(self):
            pass
    ret = _built_in_print(*objects, sep=sep, end=end, file=Writable())
    full_text = ''.join(all_text)
    _get_console().write_text(full_text)
    return ret


def write_text(text):
    """
    Write text to the AutoAuto console. This is a more "manual" version
    of the `print()` function above.
    """
    return _get_console().write_text(text)


def clear_text():
    """
    Clear the text off the AutoAuto console.
    """
    return _get_console().clear_text()


def big_image(image_id):
    """
    Display a full-screen ("big") image on the AutoAuto console.
    See `cui.CuiRoot.big_image()` for details on `image_id`.
    """
    return _get_console().big_image(image_id)


def big_status(status):
    """
    Display a large status atop the "big image". This should
    only be used after  using the `big_image()`function above.
    """
    return _get_console().big_status(status)


def big_clear():
    """
    Clear the big image and big status off the AutoAuto console.
    """
    return _get_console().big_clear()


def stream_image(rect_vals, shape, image_buf):
    """
    Steam an image buffer (`image_buf` to the AutoAuto console, specifying
    where it should show up via the `rect_vals` variable. A special
    `rect_vals` of `(0, 0, 0, 0)` indicates that the image should be
    full-screen. The `image_buf` should be either a grayscale or RGB image.
    """
    return _get_console().stream_image(tuple(rect_vals), tuple(shape), image_buf)


def clear_image():
    """
    Clear the streamed image (streamed via the `stream_image()` function above)
    off the AutoAuto console.
    """
    return _get_console().clear_image()


def clear():
    """
    Clear the AutoAuto console of all text and images.
    """
    clear_text()
    big_clear()
    clear_image()


def set_battery_percent(pct):
    """
    Set the battery percentage that is displayed on the console UI.
    `pct` should be an integer in [0, 100].
    """
    _get_console().set_battery_percent(pct)


# We won't support closing at this level (no need?),
# but if we did it would look like this:
#
#def close():
#    """
#    Close our connection to the console.
#    """
#    c = _get_console()
#    c.close()
#    global _CONSOLE
#    del _CONSOLE

