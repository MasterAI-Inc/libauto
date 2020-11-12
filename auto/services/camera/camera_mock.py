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
This modules provides mock camera class abstractions which returns random
camera frames which look like antenna noise.

This is a **synchronous** interface.
"""

import numpy as np
import time


class CameraRGB:
    """
    This class represents a mock camera which captures random noise.
    """

    def __init__(self, width=320, height=240, fps=8):
        """
        Initialize a camera object which captures frames of size `width`x`height`
        at `fps` frames-per-second.
        """
        self.width = width
        self.height = height
        self.fps = fps

    def capture(self):
        """
        Capture and return one frame from the camera as a numpy ndarray,
        or None if an error occurred.
        """
        frame = np.random.randint(0, 255, (self.height, self.width, 3), np.uint8)
        return frame

    def stream(self):
        """
        Yield frames one-at-a-time from the camera as numpy ndarrays.
        """
        while True:
            time.sleep(1/self.fps)
            frame = self.capture()
            yield frame

    def close(self):
        """
        Release the resources held by this camera object.
        """
        pass

