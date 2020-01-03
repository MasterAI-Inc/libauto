###############################################################################
#
# Copyright (c) 2017-2018 AutoAuto, LLC
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from AutoAuto, LLC.
#
###############################################################################

"""
This is an RPC server to serve the camera as a shared resource. Because of this,
multiple processes may access the camera simultaneously.
"""


try:
    from auto.camera_pi import CameraRGB
except ImportError:
    from auto.camera_cv2 import CameraRGB


from auto.rpc.server import serve


from auto import logger
log = logger.init('camera_rpc_server', terminal=True)


from threading import Thread
from queue import Queue

import asyncio
import time


# This is how long the camera will stay open _after_ the last client disconnects.
# It is common that another client will reconnect quickly after the last one disconnects,
# thus keeping the camera open for some amount of time helps make things faster for the
# next client.
CAMERA_TIMEOUT_SECONDS = 30


# Camera parameters. For options, see: http://picamera.readthedocs.io/en/release-1.10/fov.html
# If 640x480 bogs down the CPU too much, use 320x240 instead.
CAM_WIDTH = 320  # 640
CAM_HEIGHT = 240  # 480
CAM_FPS = 8


def _init_bg_capture_thread(ctl_queue, frame_callback, loop):
    def run_camera():
        event = ctl_queue.get()     # <-- block waiting for an event
        assert event == 'start'

        camera = CameraRGB(width=CAM_WIDTH, height=CAM_HEIGHT, fps=CAM_FPS)

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


def _init_interface(loop, outer_frame_callback):
    ctl_queue = Queue()
    cond = asyncio.Condition()
    frame = None

    async def frame_callback(frame_new):
        nonlocal frame
        await outer_frame_callback(frame_new)
        async with cond:
            frame = frame_new
            cond.notify_all()

    bg_thread = _init_bg_capture_thread(ctl_queue, frame_callback, loop)

    last_seen = None
    camera_on = False
    n_subscribers = 0

    class CameraRGB_RPC:
        async def export_capture(self):
            nonlocal last_seen, camera_on
            last_seen = time.time()
            if not camera_on:
                camera_on = True
                ctl_queue.put('start')
            async with cond:
                await cond.wait()
                frame_here = frame
            return frame_here

    async def subscribe(channel):
        nonlocal n_subscribers, camera_on
        n_subscribers += 1
        if n_subscribers == 1:
            if not camera_on:
                camera_on = True
                ctl_queue.put('start')
        log.info("New subscriber!")

    async def unsubscribe(channel):
        nonlocal last_seen, n_subscribers
        last_seen = time.time()
        n_subscribers -= 1
        log.info("Departed subscriber.")

    pubsub = {
        'channels': [
            'stream',
        ],
        'subscribe': subscribe,
        'unsubscribe': unsubscribe,
    }

    async def check_last_seen():
        nonlocal last_seen, n_subscribers, camera_on
        while True:
            if camera_on and n_subscribers == 0 and (time.time() - last_seen) > CAMERA_TIMEOUT_SECONDS:
                camera_on = False
                ctl_queue.put('stop')
            await asyncio.sleep(0.2)

    asyncio.create_task(check_last_seen())

    return CameraRGB_RPC, pubsub


async def init():
    loop = asyncio.get_event_loop()

    async def frame_callback(frame):
        await publish_func('stream', frame)

    root_factory, pubsub = _init_interface(loop, frame_callback)

    server, publish_func = await serve(root_factory, pubsub, 'localhost', 7001)

    log.info("RUNNING!")

    return server


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init())
    loop.run_forever()

