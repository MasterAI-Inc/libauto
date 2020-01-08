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
This client connects to the CIO RPC server. This is an **asynchronous** client.
"""

import asyncio
from auto.rpc.client import client

import cio


class CioRoot(cio.CioRoot):

    def __init__(self, inet_addr='localhost', inet_port=7002):
        self.proxy_interface = None
        self.caps = None
        self.inet_addr = inet_addr
        self.inet_port = inet_port

    async def init(self):
        if self.proxy_interface is None:
            self.proxy_interface, pubsub_channels, subscribe_func, self._close = \
                    await client(self.inet_addr, self.inet_port)
            self.caps = await self.proxy_interface.init()

        return self.caps

    async def acquire(self, capability_id):
        if self.proxy_interface is None:
            raise Exception("You must first call `init()`.")

        capability_obj = await self.proxy_interface.acquire(capability_id)
        return capability_obj

    async def release(self, capability_obj):
        if self.proxy_interface is None:
            raise Exception("You must first call `init()`.")

        rpc_guid = await capability_obj.get_rpc_guid()
        await self.proxy_interface.release(rpc_guid)

    async def close(self):
        if self.proxy_interface is not None:
            await self.proxy_interface.close()
            await self._close()
            self.proxy_interface = None


async def _run():
    cio_root = CioRoot()

    caps = await cio_root.init()
    print(caps)

    version_iface = await cio_root.acquire('VersionInfo')
    print(version_iface)
    print(await version_iface.version())
    print(await version_iface.name())

    buzzer_iface = await cio_root.acquire('Buzzer')
    print(buzzer_iface)
    await buzzer_iface.play('!T240 L8 V8 agafaea dac+adaea fa<aa<bac#a dac#adaea f4')   # "Bach's fugue in D-minor"

    led_iface = await cio_root.acquire('LEDs')
    await led_iface.set_mode('spin')
    print(led_iface)

    await buzzer_iface.wait()

    await cio_root.release(buzzer_iface)
    await cio_root.release(version_iface)
    await cio_root.release(led_iface)

    await cio_root.close()


if __name__ == '__main__':
    asyncio.run(_run())

