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
This client connects to the CUI RPC server. This is a **synchronous** client.
"""

import asyncio

from auto.services.console.client import CuiRoot as CuiRoot_async

import cui


class CuiRoot(cui.CuiRoot):

    def __init__(self, loop, inet_addr='localhost', inet_port=7003):
        self.cui_root = CuiRoot_async(inet_addr, inet_port)
        self.loop = loop

    def init(self):
        future = asyncio.run_coroutine_threadsafe(self.cui_root.init(), self.loop)
        return future.result()

    def write_text(self, text):
        future = asyncio.run_coroutine_threadsafe(self.cui_root.write_text(text), self.loop)
        return future.result()

    def clear_text(self):
        future = asyncio.run_coroutine_threadsafe(self.cui_root.clear_text(), self.loop)
        return future.result()

    def big_image(self, image_id):
        future = asyncio.run_coroutine_threadsafe(self.cui_root.big_image(image_id), self.loop)
        return future.result()

    def big_status(self, status):
        future = asyncio.run_coroutine_threadsafe(self.cui_root.big_status(status), self.loop)
        return future.result()

    def big_clear(self):
        future = asyncio.run_coroutine_threadsafe(self.cui_root.big_clear(), self.loop)
        return future.result()

    def stream_image(self, rect_vals, shape, image_buf):
        future = asyncio.run_coroutine_threadsafe(self.cui_root.stream_image(rect_vals, shape, image_buf), self.loop)
        return future.result()

    def clear_image(self):
        future = asyncio.run_coroutine_threadsafe(self.cui_root.clear_image(), self.loop)
        return future.result()

    def set_battery(self, minutes, percentage):
        future = asyncio.run_coroutine_threadsafe(self.cui_root.set_battery(minutes, percentage), self.loop)
        return future.result()

    def close(self):
        future = asyncio.run_coroutine_threadsafe(self.cui_root.close(), self.loop)
        return future.result()


def _run():
    from threading import Thread
    import time

    loop = asyncio.new_event_loop()

    def _run_event_loop():
        asyncio.set_event_loop(loop)
        loop.run_forever()

    loop_thread = Thread(target=_run_event_loop)
    loop_thread.start()

    cui_root = CuiRoot(loop)
    cui_root.init()
    cui_root.write_text('Hi!')
    time.sleep(3)
    cui_root.close()

    async def _stop_loop():
        loop.stop()

    asyncio.run_coroutine_threadsafe(_stop_loop(), loop)
    loop_thread.join()
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()


if __name__ == '__main__':
    _run()

