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
This package contains a mock implementation of the cui interface.

It is used as a fallback if no other implementations are available.
"""

import cui

from auto import logger

from threading import Lock


class CuiMock(cui.CuiRoot):
    def init(self):
        self.lock = Lock()
        self.log = logger.init('mock_cui', terminal=True)
        return True

    def write_text(self, text):
        with self.lock:
            return self.log.info("write_text({})".format(repr(text)))

    def clear_text(self):
        with self.lock:
            return self.log.info("clear_text()")

    def big_image(self, image_id):
        with self.lock:
            return self.log.info("big_image({})".format(repr(image_id)))

    def big_status(self, status):
        with self.lock:
            return self.log.info("big_status({})".format(repr(status)))

    def big_clear(self):
        with self.lock:
            return self.log.info("big_clear()")

    def stream_image(self, rect_vals, shape, image_buf):
        with self.lock:
            return self.log.info("stream_image({}, {}, buffer of length {})".format(repr(rect_vals), repr(shape), len(image_buf)))

    def clear_image(self):
        with self.lock:
            return self.log.info("clear_image()")

    def set_battery_percent(self, pct):
        with self.lock:
            return self.log.info("set_battery_percent({})".format(repr(pct)))

