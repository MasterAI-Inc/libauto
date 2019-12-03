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
This modules provides camera class abstractions which use OpenCV internally.

This is a **synchronous** interface.
"""

import cv2
import time
import weakref
import numpy as np
from threading import Thread, Condition


class CameraRGB:
    """
    This class represents a camera which captures in raw RGB.
    """

    def __init__(self, width=320, height=240, fps=8):
        """
        Initialize a camera object which captures frames of size `width`x`height`
        at `fps` frames-per-second.
        """
        self.camera = cv2.VideoCapture(0)
        self.camera.set(3, width)
        self.camera.set(4, height)
        self.fsize = (width, height)
        self.stop = False
        self.error = False
        self.frame = None
        self.cond = Condition()
        self.thread = Thread(target=_thread_main, args=(weakref.ref(self),))
        self.thread.start()

    def capture(self):
        """
        Capture and return one frame from the camera as a numpy ndarray,
        or None if an error occurred.
        """
        with self.cond:
            self.cond.wait(1.0)
            while self.frame is None and not self.stop and not self.error:
                self.cond.wait(1.0)
            if self.stop or self.error:
                frame = None
            else:
                frame = np.copy(self.frame)
        return frame

    def stream(self):
        """
        Yield frames one-at-a-time from the camera as numpy ndarrays.
        """
        while True:
            frame = self.capture()
            if frame is None:
                break
            yield frame

    def close(self):
        """
        Release the resources held by this camera object.
        """
        self.stop = True
        self.thread.join()
        self.camera.release()

    def __del__(self):
        """
        Python destructor which calls `close()` on this object.
        """
        self.close()


def _thread_main(weak_cam):
    """
    Private function which acts as the thread-main.
    Continuously reads frames from the cv2 interface.
    """
    time.sleep(1.0)
    while True:
        cam = weak_cam()
        if cam.stop:
            break
        ret, frame = cam.camera.read()
        if not ret:
            cam.error = True
            break
        frame = cv2.resize(frame, cam.fsize)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        with cam.cond:
            cam.frame = frame
            cam.cond.notifyAll()
        cam = None

