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
This package contains a PyGame implementation of the cui interface.
"""

import cui

from threading import Lock


class CuiPyGame(cui.CuiRoot):
    def init(self):
        from cui.pygame_impl import console_ui
        # If the import worked, we're good to go.
        # The import has tremendous side affects, thus
        # we delay it until this `init()` is called.
        self.lock = Lock()
        return True

    def write_text(self, text):
        with self.lock:
            return console_ui.write_text(text)

    def clear_text(self):
        with self.lock:
            return console_ui.clear_text()

    def big_image(self, image_id):
        with self.lock:
            image_path = 'images/{}.png'.format(image_id)
            return console_ui.big_image(image_path)

    def big_status(self, status):
        with self.lock:
            return console_ui.big_status(status)

    def big_clear(self):
        with self.lock:
            return console_ui.big_clear()

    def stream_image(self, rect_vals, shape, image_buf):
        with self.lock:
            return console_ui.stream_image(rect_vals, shape, image_buf)

    def clear_image(self):
        with self.lock:
            return console_ui.clear_image()

    def set_battery_percent(self, pct):
        with self.lock:
            return console_ui.set_battery_percent(pct)

