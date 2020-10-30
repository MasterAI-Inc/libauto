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
This client connects to the CUI RPC server. This is an **asynchronous** client.
"""

import asyncio
from auto.rpc.client import client

import cui


class CuiRoot(cui.CuiRoot):

    def __init__(self, inet_addr='127.0.0.1', inet_port=7003):
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

    async def set_battery(self, minutes, percentage):
        if self.proxy_interface is None:
            raise Exception("You must first call `init()`.")
        return await self.proxy_interface.set_battery(minutes, percentage)

    async def close(self):
        # Don't call `close()` on the actual `proxy_interface`, because that in turn
        # will call close on the underlying `cui_root` object, which will shut down
        # the console. We don't want that because we're treating the console as a shared
        # resource and we need it to stay open. Instead, we just close our RPC connection
        # to the RPC server to clean up the resources we're responsible for.
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

