###############################################################################
#
# Copyright (c) 2017-2021 Master AI, Inc.
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from Master AI, Inc.
#
###############################################################################

"""
This module wraps a camera in a thread and exposes an asyncio interface
for getting frames.
"""

from threading import Thread
from queue import Queue

import asyncio
import time

from auto import logger
log = logger.init(__name__, terminal=True)


def _init_bg_capture_thread(camera_factory, ctl_queue, frame_callback, loop):
    def run_camera():
        event = ctl_queue.get()     # <-- block waiting for an event
        assert event == 'start'

        camera = camera_factory()

        log.info("Initialized a camera instance...")

        for frame in camera.stream():
            frame_encoded = (frame.tobytes(), frame.shape)
            asyncio.run_coroutine_threadsafe(frame_callback(frame_encoded), loop)

            if not ctl_queue.empty():
                event = ctl_queue.get()
                assert event == 'stop'
                break

        camera.close()
        del camera

        log.info("Destroyed the camera instance...")

    def camera_thread_main():
        while True:
            run_camera()
            time.sleep(1)

    thread = Thread(target=camera_thread_main)
    thread.daemon = True     # <-- thread will exit when main thread exists
    thread.start()
    return thread


class CameraRGB_Async:
    """
    Provide an asyncio interface to a camera. A thread is created to continually capture
    frames from the camera.

    WARNING: This class is meant to be a singleton. It cannot clean itself up. It is
             meant to be instantiated once and used forever.
    """
    def __init__(self, camera_factory, loop, idle_timeout):
        self.idle_timeout = idle_timeout
        self.ctl_queue = Queue()
        self.cond = asyncio.Condition()
        self.frame = None
        self.started = False
        self.last_seen = time.time()
        self.thread = _init_bg_capture_thread(camera_factory, self.ctl_queue, self._frame_callback, loop)
        self.idle_task = asyncio.create_task(self._idle_task())

    async def capture(self):
        self.last_seen = time.time()
        if not self.started:
            self.ctl_queue.put('start')
            self.started = True
        async with self.cond:
            await self.cond.wait()
            frame_here = self.frame
        return frame_here

    async def close(self):
        if self.started:
            self.ctl_queue.put('stop')
            self.started = False

    async def _frame_callback(self, frame_new):
        async with self.cond:
            self.frame = frame_new
            self.cond.notify_all()

    async def _idle_task(self):
        while True:
            if self.started and time.time() - self.last_seen > self.idle_timeout:
                await self.close()
            await asyncio.sleep(1)

