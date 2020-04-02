import os
import sys
import shutil
import math
import time

from auto import logger
log = logger.init(__name__, terminal=True)


CURR_DIR = os.path.dirname(os.path.realpath(__file__))

sys.path.append(CURR_DIR)

import RTIMU


RTIMULIB_SETTINGS = os.environ.get('LIBAUTO_RTIMULIB_SETTINGS', '/var/lib/libauto/RTIMULib.ini')


def read():
    if not os.path.exists(RTIMULIB_SETTINGS):
        shutil.copyfile(os.path.join(CURR_DIR, 'RTIMULib.ini'), RTIMULIB_SETTINGS)

    settings = RTIMU.Settings(os.path.splitext(RTIMULIB_SETTINGS)[0])

    imu = RTIMU.RTIMU(settings)

    log.info(f'IMU Name: {imu.IMUName()}')
    log.info(f'IMU Type: {imu.IMUType()}')

    if not imu.IMUInit():
        log.info('IMU Init Failed')
        raise Exception('IMU Init Failed')

    log.info('IMU Init Succeeded')

    imu.setSlerpPower(0.02)
    imu.setGyroEnable(True)
    imu.setAccelEnable(True)
    imu.setCompassEnable(False)

    poll_interval = imu.IMUGetPollInterval()

    log.info(f'Recommended Poll Interval: {poll_interval}mS')

    while True:
        if imu.IMURead():
            data = imu.getIMUData()
            yield data
            time.sleep(poll_interval/1000.0)


if __name__ == '__main__':
    for data in read():
        if data['fusionPoseValid']:
            r, p, y = [math.degrees(v) for v in data['fusionPose']]
            print(f'\rFusion Data: r={r:.2f} p={p:.2f} y={y:.2f}', end='')

