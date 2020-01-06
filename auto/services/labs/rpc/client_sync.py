###############################################################################
#
# Copyright (c) 2017-2019 AutoAuto, LLC
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from AutoAuto, LLC.
#
###############################################################################

"""
This modules provides a **synchronous** LabsServiceIface implementation.
"""

import asyncio

from auto.services.labs.rpc.client import LabsService as LabsService_async

from auto.services.labs.rpc import LabsServiceIface


class LabsService(LabsServiceIface):

    def __init__(self, loop, inet_addr='localhost', inet_port=7004):
        self.labs = LabsService_async(inet_addr, inet_port)
        self.loop = loop

    def connect(self):
        future = asyncio.run_coroutine_threadsafe(self.labs.connect(), self.loop)
        return future.result()

    def send(self, msg):
        future = asyncio.run_coroutine_threadsafe(self.labs.send(msg), self.loop)
        return future.result()

    def close(self):
        future = asyncio.run_coroutine_threadsafe(self.labs.close(), self.loop)
        return future.result()


def _demo():
    from threading import Thread
    import time

    loop = asyncio.new_event_loop()

    def _run_event_loop():
        asyncio.set_event_loop(loop)
        loop.run_forever()

    loop_thread = Thread(target=_run_event_loop)
    loop_thread.start()

    labs = LabsService(loop)

    labs.connect()

    for i in range(5):
        did_send = labs.send({'hi': 'there'})
        print('Did Send?', did_send)

    labs.close()

    async def _stop_loop():
        loop.stop()

    asyncio.run_coroutine_threadsafe(_stop_loop(), loop)
    loop_thread.join()
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()


if __name__ == '__main__':
    _demo()

