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
This modules provides a **synchronous** camera class abstraction which pulls
frames from the camera RPC server.

For the server, see `services/camera/camera.py`.

The camera is a shared resource which can only be used by one
process at a time, thus this RPC interface is a way to allow
multiple processes to pull frames at the same time.
"""

import asyncio

from auto.services.camera.client import CameraRGB as CameraRGB_async


class CameraRGB:
    """
    This class represents a camera which captures frame in raw RGB
    from an RPC server.
    """

    def __init__(self, loop, inet_addr='localhost', inet_port=7001):
        """
        Initialize a camera object. The size of the captured frames
        will be whatever the RPC server chooses, so you should be prepared
        to deal with any sized frames.
        """
        self.camera = CameraRGB_async(inet_addr, inet_port)
        self.loop = loop
        future = asyncio.run_coroutine_threadsafe(self.camera.connect(), self.loop)
        future.result()

    def capture(self):
        """
        Capture and return one frame from the camera as a numpy ndarray.
        """
        future = asyncio.run_coroutine_threadsafe(self.camera.capture(), self.loop)
        return future.result()

    def stream(self):
        """
        Yield frames one-at-a-time from the camera as numpy ndarrays.
        """
        # TODO: A true stream... instead of calling capture() over-and-over.
        while True:
            frame = self.capture()
            yield frame

    def close(self):
        """
        Close the connection to the camera RPC server.
        """
        future = asyncio.run_coroutine_threadsafe(self.camera.close(), self.loop)
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

    cam = CameraRGB(loop)

    i = 0

    for frame in cam.stream():
        print(time.time(), frame.shape)
        i += 1
        if i == 50:
            break

    cam.close()

    async def _stop_loop():
        loop.stop()

    asyncio.run_coroutine_threadsafe(_stop_loop(), loop)
    loop_thread.join()
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()


if __name__ == '__main__':
    _demo()

