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
This module talks to the IMU on the AutoAuto controller board.
"""

import time
from threading import Thread, Condition


COND = Condition()
DATA = None


def run(verbose=False):
    curr_time = 0        # microseconds
    dt = 1000000 // 100  # data streams at 100Hz

    while True:
        accel = [0, 0, 0]
        gyro = [0, 0, 0]
        gyro_accum = [0, 0, 0]
        ahrs = [0, 0, 0]
        with COND:
            DATA = {
                'timestamp': curr_time,
                'accel': accel,
                'gyro': gyro,
                'gyro_accum': gyro_accum,
                'ahrs': ahrs,
            }
            COND.notify_all()
        curr_time += dt
        time.sleep(0.01)


def start_thread():
    thread = Thread(target=run)
    thread.daemon = True
    thread.start()
    return thread


if __name__ == '__main__':
    run(verbose=True)

