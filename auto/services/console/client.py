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
This client connects to the CUI RPC server. This is an **asynchronous** client.
"""

import asyncio
from auto.rpc.client import client

import cui


class CuiRoot(cui.CuiRoot):

    def __init__(self, inet_addr='localhost', inet_port=7003):
        self.proxy_interface = None
        self.inet_addr = inet_addr
        self.inet_port = inet_port

    async def init(self):
        if self.proxy_interface is None:
            self.proxy_interface, pubsub_channels, subscribe_func, self._close = \
                    await client(self.inet_addr, self.inet_port)
        return True

    async def write_text(self, text):
        if self.proxy_interface is None:
            raise Exception("You must first call `init()`.")
        return await self.proxy_interface.write_text(text)

    async def clear_text(self):
        if self.proxy_interface is None:
            raise Exception("You must first call `init()`.")
        return await self.proxy_interface.clear_text()

    async def big_image(self, image_id):
        if self.proxy_interface is None:
            raise Exception("You must first call `init()`.")
        return await self.proxy_interface.big_image(image_id)

    async def big_status(self, status):
        if self.proxy_interface is None:
            raise Exception("You must first call `init()`.")
        return await self.proxy_interface.big_status(status)

    async def big_clear(self):
        if self.proxy_interface is None:
            raise Exception("You must first call `init()`.")
        return await self.proxy_interface.big_clear()

    async def stream_image(self, rect_vals, shape, image_buf):
        if self.proxy_interface is None:
            raise Exception("You must first call `init()`.")
        return await self.proxy_interface.stream_image(rect_vals, shape, image_buf)

    async def clear_image(self):
        if self.proxy_interface is None:
            raise Exception("You must first call `init()`.")
        return await self.proxy_interface.clear_image()

    async def set_battery_percent(self, pct):
        if self.proxy_interface is None:
            raise Exception("You must first call `init()`.")
        return await self.proxy_interface.set_battery_percent(pct)

    async def close(self):
        """
        This is a non-standard method of the cui interface.
        It closes the underlying RPC connection.
        """
        if self.proxy_interface is not None:
            await self._close()
            self.proxy_interface = None


async def _run():
    cui_root = CuiRoot()

    await cui_root.init()

    await cui_root.write_text('Hi!')

    await asyncio.sleep(3)

    await cui_root.close()


if __name__ == '__main__':
    asyncio.run(_run())

