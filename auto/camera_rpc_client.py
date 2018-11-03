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
This modules provides a camera class abstraction which pulls
frames from an RPC server

For the server, see `startup/camera_rpc_server/camera_rpc_server.py`.

The camera is a shared resource which can only be used by one
process at a time, thus this RPC interface is a way to allow
multiple processes to pull frames at the same time.
"""

import rpyc
import numpy as np


class CameraRGB:
    """
    This class represents a camera which captures frame in raw RGB
    from an RPC server.
    """

    def __init__(self):
        """
        Initialize a camera object. The size of the captured frames
        will be whatever the RPC server chooses, so you should be prepared
        to deal with any sized frames.
        """
        self.conn = rpyc.connect("localhost", 18862, config={'sync_request_timeout': 30})
        self.conn.root.enable()

    def capture(self):
        """
        Capture and return one frame from the camera as a numpy ndarray.
        """
        buf, shape = self.conn.root.capture()
        return np.fromstring(buf, dtype=np.uint8).reshape(shape)

    def stream(self):
        """
        Yield frames one-at-a-time from the camera as numpy ndarrays.
        """
        while True:
            yield self.capture()

    def close(self):
        """
        Release the resources held by this camera object.
        """
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def __del__(self):
        """
        Python "destructor" which calls `close`. You cannot rely on this
        method to be called for you; instead you should call `close`
        yourself whenever you are finished using this camera. This
        method is only a final attempt to save you, but it cannot be
        relied upon.
        """
        self.close()

