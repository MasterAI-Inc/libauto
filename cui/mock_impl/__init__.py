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
This package contains a mock implementation of the cui interface.

It is used as a fallback if no other implementations are available.
"""

import cui
import asyncio
from auto import logger


class CuiMock(cui.CuiRoot):
    async def init(self):
        self.lock = asyncio.Lock()
        self.log = logger.init(__name__, terminal=True)
        return True

    async def write_text(self, text):
        async with self.lock:
            return self.log.info("write_text({})".format(repr(text)))

    async def clear_text(self):
        async with self.lock:
            return self.log.info("clear_text()")

    async def big_image(self, image_id):
        async with self.lock:
            return self.log.info("big_image({})".format(repr(image_id)))

    async def big_status(self, status):
        async with self.lock:
            return self.log.info("big_status({})".format(repr(status)))

    async def big_clear(self):
        async with self.lock:
            return self.log.info("big_clear()")

    async def stream_image(self, rect_vals, shape, image_buf):
        async with self.lock:
            return self.log.info("stream_image({}, {}, buffer of length {})".format(repr(rect_vals), repr(shape), len(image_buf)))

    async def clear_image(self):
        async with self.lock:
            return self.log.info("clear_image()")

    async def set_battery_percent(self, pct):
        async with self.lock:
            return self.log.info("set_battery_percent({})".format(repr(pct)))

    async def close(self):
        async with self.lock:
            return self.log.info("close()")

