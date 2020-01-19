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
Zbarlight wants you to give it a PIL image, but here at Master AI we
are cooler and we deal with straight-up numpy arrays! So, the function
below reaches further into Zbarlight to use a lower-level interface
so that we can process raw numpy arrays.
"""

from zbarlight._zbarlight import Symbologies, zbar_code_scanner
import numpy as np


def qr_scan(frame):
    if frame.dtype != np.uint8 or frame.ndim != 2:
        raise Exception("you must pass an 8-bit, 2d numpy array")
    height, width = frame.shape
    raw = frame.tobytes()
    assert(len(raw) == width*height)  # sanity
    symbologie = Symbologies.get('QRCODE')
    found = zbar_code_scanner([symbologie], raw, width, height)
    if found is None:
        return []
    return found

