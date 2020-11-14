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
This module provides a simple way to read QR codes from an image!

This is a **synchronous** interface.
"""

from zbarlight._zbarlight import Symbologies, zbar_code_scanner
import numpy as np
import cv2


def qr_scan(frame, multi=False):
    """
    Scan the `frame` for QR codes. If a QR code is found, return
    its data as a string; else, return `None`.

    When `multi=True`, this function will return a *list* of
    QR code data (allowing you to detect multiple QR codes
    within a single frame). In this case, when no QR codes are
    found, an empty list will be returned.
    """
    # Get a gray image of the proper shape:
    if frame.dtype != np.uint8:
        raise Exception("invalid dtype: {}".format(frame.dtype))
    if frame.ndim == 3:
        if frame.shape[2] == 3:
            frame_gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        elif frame.shape[2] == 1:
            frame_gray = np.squeeze(frame, axis=(2,))
        else:
            raise Exception("invalid number of color channels")
    elif frame.ndim == 2:
        frame_gray = frame
    else:
        raise Exception("invalid frame.ndim")

    """
    Note: Zbarlight wants you to give it a PIL image, but here at Master AI we
    are cooler and we deal with straight-up numpy arrays! So, the function
    below reaches further into Zbarlight to use a lower-level interface
    so that we can process raw numpy arrays.
    """
    height, width = frame_gray.shape
    raw = frame_gray.tobytes()
    assert(len(raw) == width*height)  # sanity
    symbologie = Symbologies.get('QRCODE')
    found = zbar_code_scanner([symbologie], raw, width, height)
    if found is None:
        found = []
    found = [buff.decode('utf-8') for buff in found]
    if multi:
        return found
    else:
        return found[0] if found else None

