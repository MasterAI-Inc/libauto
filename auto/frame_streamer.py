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


def plot(frames, also_stream=True, verbose=False, **fig_kwargs):
    """
    Plot the given `frames` (a numpy ndarray) into a matplotlib figure,
    returning the figure object which can be shown. This function by
    default also streams the image to your `labs` account.

    The `frames` parameter must be a numpy ndarray with one of the
    following shapes:
        - (n, h, w, 3)   meaning `n` 3-channel RGB images of size `w`x`h`
        - (n, h, w, 1)   meaning `n` 1-channel gray images of size `w`x`h`
        -    (h, w, 3)   meaning a single 3-channel RGB image of size `w`x`h`
        -    (h, w, 1)   meaning a single 1-channel gray image of size `w`x`h`
        -    (h, w)      meaning a single 1-channel gray image of size `w`x`h`
    """
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_agg import FigureCanvasAgg

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

    # need to test
    if _in_notebook():
        # Create the figure grid.
        if 'figsize' not in fig_kwargs:
            fig_kwargs['figsize'] = (5, 5) if n == 1 else (10, 10)
        fig, axes = plt.subplots(width, height, **fig_kwargs)
        canvas = FigureCanvasAgg(fig)

        # Ensure `axes` is a 1d iterable.
        try:
            axes = axes.flatten()
        except AttributeError:
            # This ^^ exception happens when width=height=1.
            axes = [axes]

        # Plot each frame into the grid.
        from itertools import zip_longest
        for ax, frame in zip_longest(axes, frames):
            if frame is not None:
                if frame.shape[2] == 1:
                    frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
                ax.imshow(frame)
            ax.axis('off')
        fig.tight_layout()
    else:
        fig = None
        axes = []

    # Also stream... if told to.
    if also_stream:
        # need to test
        montage = _create_montage(frames)
        stream(montage, to_labs=True, verbose=False)   # We say `verbose=False` here because we don't want ANOTHER printout, even if verbose is True for this `plot()` function.

    return fig, axes[:len(frames)]


def _in_notebook():
    """
    Determine if the current process is running in a jupyter notebook / iPython shell
    Returns: boolean
    """
    try:
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':
            result = True   # jupyter notebook or qtconsole
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
    Each frame shape is (height x width x 3 channels).
        frame_count | result
            1       | 1 row x 1 col
            2       | 1 row x 2 col
            3       | 2 row x 2 col (4th frame all white)
            4       | 2 row x 2 col
    Args:
        frames: list of nd-arrays

    Returns: nd array of shape (row_count * frame_height, column_count * frame_width, 3 channels)
    """
    MAX_COLS = 2
    frames = np.array(frames)
    if frames.shape[0] == 1:
        montage = frames[0]
    else:
        frames = [_shrink_img(frame, factor=1/MAX_COLS) for frame in frames]
        rows_of_frames = [frames[i:i+MAX_COLS] for i in range(0, frames.shape[0], MAX_COLS)]
        rows_of_combined_frames = [
            (np.hstack(row)
             if row.shape[0] == MAX_COLS
             else np.hstack([row[0], np.full_like(row[0],255)]))
            for row in rows_of_frames]
        montage = np.vstack(rows_of_combined_frames)
    return montage


def _shrink_img(img, factor=0.5):
    """
    Reduce the img dimensions by half.
    Args:
        img: nd array with shape (height, width, 3 channels)

    Returns: nd array with shape (height*factor, width*factor, 3)
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
            raise Exception("invalid frame ndarray ndim")
        height, width, channels = frame.shape
        shape = [width, height, channels]
        rect = [0, 0, 0, 0]
        console.stream_image(rect, shape, frame.tobytes())

    # Convert the frame to a JPG buffer and publish to the network connection.
    if to_labs:
        base64_img = base64_encode_image(frame)
        send_message_to_labs({'base64_img': base64_img})

    if verbose:
        h, w = frame.shape[:2]
        print_all("Streamed frame of size {}x{}.".format(w, h))

