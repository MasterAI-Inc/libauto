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
This modules provides an **asynchronous** camera class abstraction which pulls
frames from the camera RPC server.

For the server, see `auto/services/camera/server.py`.

The camera is a shared resource which can only be used by one
process at a time, thus this RPC interface is a way to allow
multiple processes to pull frames at the same time.
"""

import numpy as np
import asyncio

from auto.rpc.client import client


class CameraRGB:
    """
    This class represents a camera which captures frame in raw RGB
    from an RPC server.
    """

    def __init__(self, inet_addr='localhost', inet_port=7001):
        """
        Initialize a camera object. The size of the captured frames
        will be whatever the RPC server chooses, so you should be prepared
        to deal with any sized frames.
        """
        self.inet_addr = inet_addr
        self.inet_port = inet_port
        self.is_connected = False

    async def connect(self):
        """
        Connect the camera RPC server.
        """
        if not self.is_connected:
            self._proxy_interface, self._pubsub_channels, self._subscribe_func, self._close = \
                    await client(self.inet_addr, self.inet_port)
            self.is_connected = True

    async def capture(self):
        """
        Capture and return one frame from the camera as a numpy ndarray.
        """
        if not self.is_connected:
            raise Exception("You must first call `connect()` before you can call `capture()`.")
        buf, shape = await self._proxy_interface.capture()
        return np.frombuffer(buf, dtype=np.uint8).reshape(shape)

    async def stream(self):
        """
        Yield frames one-at-a-time from the camera as numpy ndarrays.
        """
        if not self.is_connected:
            raise Exception("You must first call `connect()` before you can call `stream()`.")
        q = asyncio.Queue()
        async def callback(channel, payload):
            buf, shape = payload
            frame = np.frombuffer(buf, dtype=np.uint8).reshape(shape)
            await q.put(frame)
        unsubscribe_func = await self._subscribe_func('stream', callback)
        try:
            while True:
                frame = await q.get()
                yield frame
        finally:
            await unsubscribe_func()

    async def release(self):
        """
        Instruct the underlying camera driver to be release the camera
        resource. This is *not* permanent. You may still call capture
        after this, and the camera will be re-acquired at that time.

        This is a non-standard part of the camera interface. It is
        only used in this RPC setting.
        """
        if not self.is_connected:
            raise Exception("You must first call `connect()` before you can call `release()`.")
        return await self._proxy_interface.release()

    async def close(self):
        """
        Close the connection to the camera RPC server.
        This is permanent; you must obtain a new connection
        to regain access to the camera.
        """
        if self.is_connected:
            self.is_connected = False
            await self._close()


async def _demo():
    cam = CameraRGB()
    await cam.connect()

    i = 0

    import time

    async for frame in cam.stream():
        print(time.time(), frame.shape)
        i += 1
        if i == 50:
            break

    await cam.close()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_demo())
    loop.run_until_complete(loop.shutdown_asyncgens())

    # Running the loop "forever" (`loop.run_forever()`) will _also_ shutdown async generators,
    # but then you are stuck with a forever-running-loop! The call above allows us to tear
    # down everything cleanly (including generator finally blocks) before the program terminates.

