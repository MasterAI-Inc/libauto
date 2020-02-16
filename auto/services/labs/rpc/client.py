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
This modules provides an **asynchronous** LabsServiceIface implementation.
"""

import asyncio

from auto.rpc.client import client

from auto.services.labs.rpc import LabsServiceIface


class LabsService(LabsServiceIface):

    def __init__(self, inet_addr='localhost', inet_port=7004):
        self.inet_addr = inet_addr
        self.inet_port = inet_port
        self.is_connected = False
        self.is_subscribed = False

    async def connect(self):
        if not self.is_connected:
            self._proxy_interface, self._pubsub_channels, self._subscribe_func, self._close = \
                    await client(self.inet_addr, self.inet_port)
            self.is_connected = True

    async def send(self, msg):
        if not self.is_connected:
            raise Exception("You must first call `connect()` before you can call `send()`.")
        return await self._proxy_interface.send(msg)

    async def receive(self):
        if not self.is_connected:
            raise Exception("You must first call `connect()` before you can call `receive()`.")
        if not self.is_subscribed:
            self.is_subscribed = True
            self.inbound_message_queue = asyncio.Queue()
            _ = await self._subscribe_func('messages', self._new_message_callback)
        return await self.inbound_message_queue.get()

    async def close(self):
        if self.is_connected:
            self.is_connected = False
            await self._close()

    async def _new_message_callback(self, channel, msg):
        await self.inbound_message_queue.put(msg)


async def _demo():
    labs = LabsService()
    await labs.connect()

    for i in range(5):
        did_send = await labs.send({'hi': 'there'})
        print('Did Send?', did_send)

    await labs.close()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_demo())
    loop.run_until_complete(loop.shutdown_asyncgens())

    # Running the loop "forever" (`loop.run_forever()`) will _also_ shutdown async generators,
    # but then you are stuck with a forever-running-loop! The call above allows us to tear
    # down everything cleanly (including generator finally blocks) before the program terminates.

