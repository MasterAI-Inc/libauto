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
This module provides the default, easy, global camera interface.
Internally, it obtains frames by querying the camera RPC server.

This is a **synchronous** interface.
"""

import os
import cv2
import base64
import numpy as np

import auto
from auto.capabilities import list_caps, acquire, release
from auto import IS_VIRTUAL


class _CameraRGB:
    def __init__(self, camera):
        self._camera = camera
        self.frame_index = 0
        self.text_scale = 0.75
        self.text_color = [255, 255, 255]
        self.text_line_width = 2

    def capture(self):
        buf, shape = self._camera.capture()
        frame = np.frombuffer(buf, dtype=np.uint8).reshape(shape)
        draw_frame_index(
                frame,
                self.frame_index,
                self.text_scale,
                self.text_color,
                self.text_line_width
        )
        self.frame_index += 1
        return frame

    def stream(self):
        while True:
            frame = self.capture()
            yield frame


def global_camera(verbose=False):
    """
    Creates (for the first call) or retrieves (for later calls) the
    global camera object. This is a convenience function to facilitate
    quickly and easily creating and retrieving a camera singleton.
    """
    global GLOBAL_CAMERA
    try:
        GLOBAL_CAMERA
    except NameError:
        caps = list_caps()
        if 'Camera' not in caps:
            raise AttributeError("This device does not have a Camera.")
        camera = acquire('Camera')
        GLOBAL_CAMERA = _CameraRGB(camera)
        if verbose:
            auto._ctx_print_all("Instantiated a global camera object!")
    return GLOBAL_CAMERA


def close_global_camera(verbose=False):
    """
    Close and delete the global camera object.
    """
    global GLOBAL_CAMERA
    try:
        GLOBAL_CAMERA   # <-- just to see if it exists
        if verbose:
            auto._ctx_print_all("Closing the global camera object...")
        release(GLOBAL_CAMERA._camera)
        del GLOBAL_CAMERA
    except NameError:
        # There is no global camera, so nothing needs to be done.
        pass


def capture(num_frames=1, verbose=False):
    """
    Capture `num_frames` frames from the (global) camera and return
    them as a numpy ndarray.

    This is a convenience function to make the most common use-case simpler.
    """
    camera = global_camera(verbose)

    if num_frames > 1:
        frames = np.array([frame for _, frame in zip(range(num_frames), camera.stream())])
        if verbose:
            auto._ctx_print_all("Captured {} frames.".format(num_frames))
        return frames
    else:
        frame = camera.capture()
        if verbose:
            auto._ctx_print_all("Captured 1 frame.")
        return frame


def draw_frame_index(frame, index,
                     text_scale=0.75,
                     text_color=[255, 255, 255],
                     text_line_width=2):
    text = "frame {}".format(index)
    x = 5
    y = frame.shape[0] - 5
    cv2.putText(frame,
                text,
                (x, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                text_scale,
                text_color,
                text_line_width)


def base64_encode_image(frame):
    """
    Encodes an image buffer (an ndarray) as a base64 encoded string.
    """
    if frame.ndim == 2:
        frame = np.expand_dims(frame, axis=2)
        assert frame.ndim == 3 and frame.shape[2] == 1
    elif frame.ndim == 3:
        if frame.shape[2] == 1:
            pass # all good
        elif frame.shape[2] == 3:
            # cv2.imencode expects a BGR image:
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            assert frame.ndim == 3 and frame.shape[2] == 3
        else:
            raise Exception("invalid number of channels")
    else:
        raise Exception("invalid frame ndarray ndim")
    if IS_VIRTUAL:
        png_img = cv2.imencode('.png', frame, [cv2.IMWRITE_PNG_COMPRESSION, 6])[1].tobytes()
        base64_img = 'data:image/png;base64,' + base64.b64encode(png_img).decode('ascii')
    else:
        jpg_img = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])[1].tobytes()
        base64_img = 'data:image/jpeg;base64,' + base64.b64encode(jpg_img).decode('ascii')
    return base64_img

