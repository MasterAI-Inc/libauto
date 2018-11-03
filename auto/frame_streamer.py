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

    # Also stream... if told to.
    if also_stream:
        if n > 1:
            canvas.draw()
            canvas_width, canvas_height = [int(v) for v in fig.get_size_inches() * fig.get_dpi()]
            canvas_frame = np.fromstring(canvas.tostring_rgb(), dtype='uint8').reshape(canvas_height, canvas_width, 3)
            stream(canvas_frame, to_labs=True, verbose=False)  # We say `verbose=False` here because we don't want ANOTHER printout, even if verbose is True for this `plot()` function.
        else:
            stream(frames[0], to_labs=True, verbose=False)     # ... same ...

    return fig, axes[:len(frames)]


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

