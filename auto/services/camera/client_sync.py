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
This modules provides a **synchronous** camera class abstraction which pulls
frames from the camera RPC server.

For the server, see `auto/services/camera/server.py`.

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

    def release(self):
        """
        Instruct the underlying camera driver to be release the camera
        resource. This is *not* permanent. You may still call capture
        after this, and the camera will be re-acquired at that time.

        This is a non-standard part of the camera interface. It is
        only used in this RPC setting.
        """
        future = asyncio.run_coroutine_threadsafe(self.camera.release(), self.loop)
        return future.result()

    def close(self):
        """
        Close the connection to the camera RPC server.
        This is permanent; you must obtain a new connection
        to regain access to the camera.
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

