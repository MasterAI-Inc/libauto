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
This package contains the interface to your robot's Console UI, most likely
running on your device's LDC screen.

Its name is CUI (Console User Interface).
"""

import abc


class CuiRoot(abc.ABC):
    """
    This is the front-door interface of the Console UI ("cui"). You begin
    by `init()`ing it, and if successful, you may then use the other methods
    defined below.
    """

    @abc.abstractmethod
    async def init(self):
        """
        Initialize the Console UI. If successful, this method returns True,
        otherwise it raises an exception indicating that this particular
        implementation cannot run on your device.
        """
        pass

    @abc.abstractmethod
    async def write_text(self, text):
        """
        Write text to the console.
        """
        pass

    @abc.abstractmethod
    async def clear_text(self):
        """
        Clear all text from the console.
        """
        pass

    @abc.abstractmethod
    async def big_image(self, image_id):
        """
        Display a big image having the id `image_path`.
        Standard image IDs are:
            - "wifi_error"    : Show that there was a WiFi connection error.
            - "wifi_pending"  : Show that WiFi is attempting to connect.
            - "wifi_success"  : Show that WiFi successfully connected!
            - "pair_error"    : Show that the pairing process failed.
            - "pair_pending"  : Show that the pairing process is in-progress.
            - "pair_success"  : Show that the pairing process was a success!
            - "token_error"   : Show that the device needs a token installed.
            - "token_success" : Show that a new token was installed successfully!
        """
        pass

    @abc.abstractmethod
    async def big_status(self, status):
        """
        Display a big status as text covering the console and
        any image which may be shown.
        """
        pass

    @abc.abstractmethod
    async def big_clear(self):
        """
        Clear the big image and big status.
        """
        pass

    @abc.abstractmethod
    async def stream_image(self, rect_vals, shape, image_buf):
        """
        Display the streamed image in `image_buf` in the area
        on the screen described by `rect_vals`. The image has
        shape `shape`.
        """
        pass

    @abc.abstractmethod
    async def clear_image(self):
        """
        Clear the streamed image from the screen.
        """
        pass

    @abc.abstractmethod
    async def set_battery_percent(self, pct):
        """
        `pct` should be an integer in [0, 100].
        """
        pass

    @abc.abstractmethod
    async def close(self):
        """
        Close the console (remove the window, clear resources, etc.)
        """
        pass

