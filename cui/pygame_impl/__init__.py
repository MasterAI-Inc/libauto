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
This package contains a PyGame implementation of the cui interface.
"""

import cui
import asyncio


class CuiPyGame(cui.CuiRoot):
    async def init(self):
        from cui.pygame_impl import console_ui
        # If the import worked, we're good to go.
        # The import has tremendous side affects, thus
        # we delay it until this `init()` is called.
        self.lock = asyncio.Lock()
        self.loop = asyncio.get_running_loop()
        self.event_task = asyncio.create_task(self._check_events())
        return True

    async def write_text(self, text):
        async with self.lock:
            return await self.loop.run_in_executor(
                    None,
                    console_ui.write_text,
                    text
            )

    async def clear_text(self):
        async with self.lock:
            return await self.loop.run_in_executor(
                    None,
                    console_ui.clear_text,
            )

    async def big_image(self, image_id):
        async with self.lock:
            image_path = 'images/{}.png'.format(image_id)
            return await self.loop.run_in_executor(
                    None,
                    console_ui.big_image,
                    image_path
            )

    async def big_status(self, status):
        async with self.lock:
            return await self.loop.run_in_executor(
                    None,
                    console_ui.big_status,
                    status
            )

    async def big_clear(self):
        async with self.lock:
            return await self.loop.run_in_executor(
                    None,
                    console_ui.big_clear,
            )

    async def stream_image(self, rect_vals, shape, image_buf):
        async with self.lock:
            return await self.loop.run_in_executor(
                    None,
                    console_ui.stream_image,
                    rect_vals, shape, image_buf
            )

    async def clear_image(self):
        async with self.lock:
            return await self.loop.run_in_executor(
                    None,
                    console_ui.clear_image,
            )

    async def set_battery(self, minutes, percentage):
        async with self.lock:
            return await self.loop.run_in_executor(
                    None,
                    console_ui.set_battery,
                    minutes, percentage
            )

    async def close(self):
        async with self.lock:
            return await self.loop.run_in_executor(
                    None,
                    console_ui.close,
            )

    async def _check_events(self):
        while True:
            async with self.lock:
                await self.loop.run_in_executor(
                        None,
                        console_ui.check_events,
                )
            await asyncio.sleep(0.2)

