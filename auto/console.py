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
Module to interface with your AutoAuto device's front-panel console via RPC.

For the server, see `startup/console_ui/console_ui.py`.
"""


import rpyc
CONN = rpyc.connect("localhost", 18863, config={'sync_request_timeout': 30})


_built_in_print = print


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
    CONN.root.write_text(''.join(all_text))
    return ret


def write_text(text):
    """
    Write text to the AutoAuto console. This is a more "manual" version
    of the `print()` function above.
    """
    return CONN.root.write_text(text)


def clear_text():
    """
    Clear the text off the AutoAuto console.
    """
    return CONN.root.clear_text()


def big_image(image_path):
    """
    Display a full-screen ("big") image on the AutoAuto console.
    The image must be one on disk (probably in the `resources/`
    directory) and you give a path to that image (relative to the
    libauto repo root) to this function.
    """
    return CONN.root.big_image(image_path)


def big_status(status):
    """
    Display a large status atop the "big image". This should
    only be used after  using the `big_image()`function above.
    """
    return CONN.root.big_status(status)


def big_clear():
    """
    Clear the big image and big status off the AutoAuto console.
    """
    return CONN.root.big_clear()


def stream_image(rect_vals, shape, image_buf):
    """
    Steam an image buffer (`image_buf` to the AutoAuto console, specifying
    where it should show up via the `rect_vals` variable. A special
    `rect_vals` of `(0, 0, 0, 0)` indicates that the image should be
    full-screen. The `image_buf` should be either a grayscale or RGB image.
    """
    return CONN.root.stream_image(tuple(rect_vals), tuple(shape), image_buf)


def clear_image():
    """
    Clear the streamed image (streamed via the `stream_image()` function above)
    off the AutoAuto console.
    """
    return CONN.root.clear_image()


def clear():
    """
    Clear the AutoAuto console of all text and images.
    """
    clear_text()
    big_clear()
    clear_image()

