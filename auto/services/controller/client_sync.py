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
This client connects to the CIO RPC server. This is a **synchronous** client.
"""

import asyncio

from auto.asyncio_tools import wrap_async_to_sync

from auto.services.controller.client import CioRoot as CioRoot_async

import cio


class CioRoot(cio.CioRoot):

    def __init__(self, loop, inet_addr='localhost', inet_port=7002):
        self.cio_root = CioRoot_async(inet_addr, inet_port)
        self.loop = loop

    def init(self):
        future = asyncio.run_coroutine_threadsafe(self.cio_root.init(), self.loop)
        return future.result()

    def acquire(self, capability_id):
        future = asyncio.run_coroutine_threadsafe(self.cio_root.acquire(capability_id), self.loop)
        capability_obj = future.result()
        wrapped_capability_obj = wrap_async_to_sync(capability_obj, self.loop)
        wrapped_capability_obj._original_capability_obj = capability_obj
        return wrapped_capability_obj

    def release(self, capability_obj):
        wrapped_capability_obj = capability_obj
        capability_obj = wrapped_capability_obj._original_capability_obj
        future = asyncio.run_coroutine_threadsafe(self.cio_root.release(capability_obj), self.loop)
        return future.result()

    def close(self):
        future = asyncio.run_coroutine_threadsafe(self.cio_root.close(), self.loop)
        return future.result()


def _run():
    from threading import Thread

    loop = asyncio.new_event_loop()

    def _run_event_loop():
        asyncio.set_event_loop(loop)
        loop.run_forever()

    loop_thread = Thread(target=_run_event_loop)
    loop_thread.start()

    cio_root = CioRoot(loop)

    caps = cio_root.init()
    print(caps)

    version_iface = cio_root.acquire('VersionInfo')
    print(version_iface)
    print(version_iface.version())
    print(version_iface.name())

    buzzer_iface = cio_root.acquire('Buzzer')
    print(buzzer_iface)
    buzzer_iface.play('!T240 L8 V8 agafaea dac+adaea fa<aa<bac#a dac#adaea f4')   # "Bach's fugue in D-minor"

    led_iface = cio_root.acquire('LEDs')
    led_iface.set_mode('spin')
    print(led_iface)

    buzzer_iface.wait()

    cio_root.release(buzzer_iface)
    cio_root.release(version_iface)
    cio_root.release(led_iface)

    cio_root.close()

    async def _stop_loop():
        loop.stop()

    asyncio.run_coroutine_threadsafe(_stop_loop(), loop)
    loop_thread.join()
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()


if __name__ == '__main__':
    _run()

