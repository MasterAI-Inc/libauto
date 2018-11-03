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
This modules provides camera class abstractions which use the `picamera`
library internally.
"""

from picamera import PiCamera
from picamera.array import PiRGBArray
import time


class CameraRGB:
    """
    This class represents a camera which captures in raw RGB.
    """

    def __init__(self, width=320, height=240, fps=8):
        """
        Initialize a camera object which captures frames of size `width`x`height`
        at `fps` frames-per-second.
        """
        self.camera = PiCamera(resolution=(width, height), framerate=fps)
        self.array = PiRGBArray(self.camera, size=(width, height))
        time.sleep(1.0)

    def capture(self):
        """
        Capture and return one frame from the camera as a numpy ndarray,
        or None if an error occurred.
        """
        self.camera.capture(self.array, format='rgb', use_video_port=True)
        frame = self.array.array
        self.array.truncate(0)
        return frame

    def stream(self):
        """
        Yield frames one-at-a-time from the camera as numpy ndarrays.
        """
        for _ in self.camera.capture_continuous(self.array,
                                                format='rgb',
                                                use_video_port=True):
            frame = self.array.array
            self.array.truncate(0)
            yield frame

    def close(self):
        """
        Release the resources held by this camera object.
        """
        self.camera.close()

    def __del__(self):
        """
        Python destructor which calls `close()` on this object.
        """
        self.close()

