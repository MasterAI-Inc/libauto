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
This module provides helper functions for plotting and streaming camera
frames, or for plotting/streaming any RGB or grey image buffer.
"""

from auto import console
from auto import print_all
from auto.labs import send_message_to_labs
from auto.camera import base64_encode_image

import cv2
import numpy as np
import PIL.Image

OPTIMAL_ASPECT_RATIO = 4/3


def plot(frames, also_stream=True, verbose=False):
    """
    Stitch together the given `frames` (a numpy nd-array) into a single nd-array.
    If running in a notebook then the PIL image will be returned (and displayed).
    This function by default also streams the image to your `labs` account.

    The `frames` parameter must be a numpy ndarray with one of the
    following shapes:
        - (n, h, w, 3)   meaning `n` 3-channel RGB images of size `w`x`h`
        - (n, h, w, 1)   meaning `n` 1-channel gray images of size `w`x`h`
        -    (h, w, 3)   meaning a single 3-channel RGB image of size `w`x`h`
        -    (h, w, 1)   meaning a single 1-channel gray image of size `w`x`h`
        -    (h, w)      meaning a single 1-channel gray image of size `w`x`h`
    """

    # Ensure the proper shape of `frames`.
    if frames.ndim == 4:
        pass
    elif frames.ndim == 3:
        frames = np.expand_dims(frames, axis=0)
    elif frames.ndim == 2:
        frames = np.expand_dims(frames, axis=2)
        frames = np.expand_dims(frames, axis=0)
    else:
        raise Exception("invalid frames ndarray ndim")
    if frames.shape[3] != 3 and frames.shape[3] != 1:
        raise Exception("invalid number of channels")

    # Compute the figure grid size (this will be (height x width) subplots).
    n = frames.shape[0]
    width = int(round((float(n)**0.5)))
    height = n // width
    if (n % width) > 0:
        height += 1
    if verbose:
        print_all("Plotting {} frame{}...".format(n, 's' if n != 1 else ''))

    montage = _create_montage(frames)

    if _in_notebook():
        result_obj = PIL.Image.fromarray(montage)
    else:
        result_obj = None

    # Also stream... if told to.
    if also_stream:
        stream(montage, to_labs=True, verbose=False)   # We say `verbose=False` here because we don't want ANOTHER printout, even if verbose is True for this `plot()` function.

    return result_obj


def _in_notebook():
    """
    Determine if the current process is running in a jupyter notebook / iPython shell
    Returns: boolean
    """
    try:
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':
            result = True   # jupyter notebook
        elif shell == 'TerminalInteractiveShell':
            result = True   # iPython via terminal
        else:
            result = False  # unknown shell type
    except NameError:
        result = False      # most likely standard Python interpreter
    return result


def _create_montage(frames):
    """
    Stitch together all frames into 1 montage image:
    Each frame shape is (height x width x channels).
        frame_count | result
            1       | 1 row x 1 col
            2       | 1 row x 2 col
            3       | 2 row x 2 col (4th frame all white)
            4       | 2 row x 2 col
    Args:
        frames: list of nd-arrays

    Returns: nd-array of shape (row_count * frame_height, column_count * frame_width, channels)
    """
    MAX_COLS = 2
    frames = np.array(frames)
    if frames.shape[0] == 1:
        montage = frames[0]
    else:
        frames = [_shrink_img(frame, factor=1/MAX_COLS) for frame in frames]
        rows_of_frames = [frames[i:i+MAX_COLS] for i in range(0, len(frames), MAX_COLS)]
        rows_of_combined_frames = [(np.hstack(row) if len(row) == MAX_COLS             # stitch frames together
                                    else np.hstack([row[0], np.full_like(row[0],255)]) # stitch frame with white frame
                                   ) for row in rows_of_frames]
        montage = np.vstack(rows_of_combined_frames)
    return montage


def _shrink_img(img, factor=0.5):
    """
    Reduce the img dimensions to factor*100 percent.
    Args:
        img: nd-array with shape (height, width, channels)

    Returns: nd-array with shape (height*factor, width*factor, channels)
    """
    shrunk_image = cv2.resize(img,None,fx=factor,fy=factor,interpolation=cv2.INTER_AREA)
    return shrunk_image


def stream(frame, to_console=True, to_labs=False, verbose=False):
    """
    Stream the given `frame` (a numpy ndarray) to your device's
    console _and_ (optionally) to your `labs` account to be shown
    in your browser.

    The `frame` parameter must be a numpy ndarray with one of the
    following shapes:
        - (h, w, 3)   meaning a single 3-channel RGB image of size `w`x`h`
        - (h, w, 1)   meaning a single 1-channel gray image of size `w`x`h`
        - (h, w)      meaning a single 1-channel gray image of size `w`x`h`
    """
    if frame is None:
        if to_console:
            console.clear_image()
        if to_labs:
            send_message_to_labs({'base64_img': ''})
        return

    # Publish the uncompressed frame to the console UI.
    if to_console:
        if frame.ndim == 3:
            if frame.shape[2] == 3:
                pass  # all good
            elif frame.shape[2] == 1:
                pass  # all good
            else:
                raise Exception("invalid number of channels")
        elif frame.ndim == 2:
            frame = np.expand_dims(frame, axis=2)
            assert frame.ndim == 3 and frame.shape[2] == 1
        else:
            raise Exception(f"invalid frame ndarray ndim: {frame.ndim}")
        height, width, channels = frame.shape
        aspect_ratio = width / height
        if aspect_ratio != OPTIMAL_ASPECT_RATIO:
            final_frame = _add_white_bars(frame)
            height, width, channels = final_frame.shape
        else:
            final_frame = frame
        shape = [width, height, channels]
        rect = [0, 0, 0, 0]
        console.stream_image(rect, shape, final_frame.tobytes())

    # Convert the frame to a JPG buffer and publish to the network connection.
    if to_labs:
        base64_img = base64_encode_image(frame)
        send_message_to_labs({'base64_img': base64_img})

    if verbose:
        h, w = frame.shape[:2]
        print_all("Streamed frame of size {}x{}.".format(w, h))


def _add_white_bars(frame):
    """
    This function is intended for a wide image that needs white bars
    on top and bottom so as to not be stretched when displayed full
    screen on the car display.
    Args:
        frame: nd-array (height, width, channels)

    Returns: nd-array (height, width, channels) with the OPTIMAL_ASPECT_RATIO
    """
    height, width, channels = frame.shape
    aspect_ratio = width / height
    if aspect_ratio > OPTIMAL_ASPECT_RATIO:
        # add horizontal bars
        bar_height = int(((width / OPTIMAL_ASPECT_RATIO) - height )/ 2)
        bar = np.ones((bar_height, width, channels), dtype=frame.dtype) * 255
        frame = np.vstack((bar, frame, bar))
    else:
        # add vertical bars
        pass
    return frame