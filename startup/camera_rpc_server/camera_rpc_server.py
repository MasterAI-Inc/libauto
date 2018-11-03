###############################################################################
#
# Copyright (c) 2017-2018 AutoAuto, LLC
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from AutoAuto, LLC.
#
###############################################################################

try:
    from auto.camera_pi import CameraRGB
except ImportError:
    from auto.camera_cv2 import CameraRGB

import rpyc
import time
from threading import Thread, Condition

from auto import logger
log = logger.init('camera_rpc_server', terminal=True)


# This is how long the camera will stay open _after_ the last client disconnects.
# It is common that another client will reconnect quickly after the last one disconnects,
# thus keeping the camera open for some amount of time helps make things faster for the
# next client.
CAMERA_TIMEOUT_SECONDS = 60


# Camera parameters. For options, see: http://picamera.readthedocs.io/en/release-1.10/fov.html
# Consider 640x480 or 320x240. Unfortunately, 640x480 seems to bog-down the CPU too much.
CAM_WIDTH = 320
CAM_HEIGHT = 240
CAM_FPS = 8


# Global synchronized state.
CLIENT_SET = set()
FRAME = None
COND = Condition()


class CameraService(rpyc.Service):

    def __init__(self):
        pass

    def on_connect(self, conn):
        self.conn = conn
        self.conn_name = self.conn._config["connid"]
        with COND:
            log.info("New client: {}".format(self.conn_name))

    def exposed_enable(self):
        with COND:
            CLIENT_SET.add(self.conn)
            log.info("Client {} enabled the camera!".format(self.conn_name))

    def on_disconnect(self, conn):
        with COND:
            if self.conn in CLIENT_SET:
                CLIENT_SET.remove(self.conn)
            log.info("Dead client: {}".format(self.conn_name))

    def exposed_capture(self):
        with COND:
            COND.wait()
            log.info('Client requested frame, got it!')
            return FRAME.tobytes(), FRAME.shape


def _capture_forever():
    time_last_client_seen = None
    camera = None
    global FRAME

    while True:
        with COND:
            n_clients = len(CLIENT_SET)

        curr_time = time.time()

        if n_clients > 0 and camera is None:
            camera = CameraRGB(width=CAM_WIDTH, height=CAM_HEIGHT, fps=CAM_FPS)
            with COND:
                log.info("Opened the camera!")

        if n_clients == 0 and camera is not None and (curr_time - time_last_client_seen) > CAMERA_TIMEOUT_SECONDS:
            camera.close()
            camera = None
            with COND:
                log.info("Closed the camera...")

        if n_clients > 0:
            time_last_client_seen = curr_time

        if camera is not None:
            frame = camera.capture()
            with COND:
                FRAME = frame.copy()
                log.info("Captured a frame with shape {}".format(frame.shape))
                COND.notify_all()
        else:
            time.sleep(0.05)


if __name__ == "__main__":

    from rpyc.utils.server import ThreadedServer

    rpc_server = ThreadedServer(CameraService, port=18862)

    prc_server_thread = Thread(target=rpc_server.start)
    prc_server_thread.start()

    with COND:
        log.info("RUNNING!")

    _capture_forever()

