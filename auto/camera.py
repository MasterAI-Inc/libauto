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
This module provides the default, easy, global camera interface.
Internally, it obtains frames by querying the camera RPC server.
"""

import cv2
import base64
import numpy as np

import auto
from auto.camera_rpc_client import CameraRGB


def global_camera(verbose=False):
    """
    Creates (for the first call) or retrieves (for later calls) the
    global camera object. This is a convenience function to facilitate
    quickly and easily building a camera singleton.
    """
    global GLOBAL_CAMERA
    try:
        return GLOBAL_CAMERA
    except NameError:
        GLOBAL_CAMERA = wrap_frame_index_decorator(CameraRGB())
        if verbose:
            auto.print_all("Instantiated a camera object!")
        return GLOBAL_CAMERA


def capture(num_frames=1, verbose=False):
    """
    Capture `num_frames` frames from the (global) camera and return
    them as a numpy ndarray.

    This is a convenience function to make the most common use-case simpler.
    """
    camera = global_camera(verbose)

    if num_frames > 1:
        frames = []
        for _, frame in zip(range(num_frames), camera.stream()):
            frames.append(frame)
        frames = np.array(frames)
        if verbose:
            auto.print_all("Captured {} frames.".format(num_frames))
        return frames

    else:
        frame = camera.capture()
        if verbose:
            auto.print_all("Captured 1 frame.")
        return frame


def wrap_frame_index_decorator(camera):
    """
    Wrap `camera` in a decorator which draws the frame index onto
    each from once captured from the camera.
    Returns a camera-like object.
    """
    class CameraRGBFrameIndexDecorator:
        def __init__(self,
                     decorated,
                     text_scale=0.75,
                     text_color=[255, 255, 255],
                     text_line_width=2):
            self.decorated = decorated
            self.frame_index = 0
            self.text_scale = text_scale
            self.text_color = text_color
            self.text_line_width = text_line_width

        def _draw_frame_index(self, frame):
            text = "frame {}".format(self.frame_index)
            self.frame_index += 1
            x = 5
            y = frame.shape[0] - 5
            cv2.putText(frame,
                        text,
                        (x, y),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        self.text_scale,
                        self.text_color,
                        self.text_line_width)

        def capture(self):
            frame = self.decorated.capture()
            self._draw_frame_index(frame)
            return frame

        def stream(self):
            for frame in self.decorated.stream():
                self._draw_frame_index(frame)
                yield frame

        def close(self):
            return self.decorated.close()

    return CameraRGBFrameIndexDecorator(camera)


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
    jpg_img = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])[1].tobytes()
    base64_img = 'data:image/jpeg;base64,' + base64.b64encode(jpg_img).decode('ascii')
    return base64_img

