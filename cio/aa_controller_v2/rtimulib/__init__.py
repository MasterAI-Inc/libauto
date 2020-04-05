import os
import sys
import shutil
import math
import time

from threading import Thread, Lock

from auto import logger
log = logger.init(__name__, terminal=True)


CURR_DIR = os.path.dirname(os.path.realpath(__file__))
RTIMULIB_SETTINGS = os.environ.get('LIBAUTO_RTIMULIB_SETTINGS', '/var/lib/libauto/RTIMULib.ini')
LOCK = Lock()
DATA = None
IS_WORKING = None


def canonical_radians(val):
    while val <= -math.pi:
        val += 2*math.pi
    while val > math.pi:
        val -= 2*math.pi
    return val


class GyroAccumulator:
    def __init__(self):
        self.last_t = None
        self.gyro_accum = 0.0, 0.0, 0.0

    def update(self, t, gyro):
        dt = ((t - self.last_t) if self.last_t is not None else 0.0) * 0.000001
        self.last_t = t
        self.gyro_accum = tuple([canonical_radians(ga + g*dt) for ga, g in zip(self.gyro_accum, gyro)])
        return self.gyro_accum


def _fix(data):
    # The RTIMULib library does wack things with the axis directions.
    # See: https://github.com/RPi-Distro/RTIMULib/blob/b949681af69b45f0f7f4bb53b6770037b5b02178/RTIMULib/IMUDrivers/RTIMUMPU9150.cpp#L577-L585
    # We need to reverse this.
    x, y, z = data['gyro']
    data['gyro'] = x, -y, -z
    x, y, z = data['accel']
    data['accel'] = -x, y, z
    for v in data['gyro']:
        if abs(v) > 600:
            return False  # bad data
    for v in data['accel']:
        if abs(v) > 5:
            return False  # bad data
    return True


def read():
    global IS_WORKING

    sys.path.append(CURR_DIR)
    import RTIMU  # <-- intentionally delaying this import because we only want it loaded when we're sure we need it

    if not os.path.exists(RTIMULIB_SETTINGS):
        shutil.copyfile(os.path.join(CURR_DIR, 'RTIMULib.ini'), RTIMULIB_SETTINGS)

    settings = RTIMU.Settings(os.path.splitext(RTIMULIB_SETTINGS)[0])

    imu = RTIMU.RTIMU(settings)

    log.info(f'IMU Name: {imu.IMUName()}')
    log.info(f'IMU Type: {imu.IMUType()}')

    if not imu.IMUInit():
        log.info('IMU Init Failed')
        IS_WORKING = False
        raise Exception('IMU Init Failed')

    log.info('IMU Init Succeeded')
    IS_WORKING = True

    imu.setSlerpPower(0.02)
    imu.setGyroEnable(True)
    imu.setAccelEnable(True)
    imu.setCompassEnable(False)

    poll_interval = imu.IMUGetPollInterval()

    log.info(f'Recommended Poll Interval: {poll_interval}mS')

    gyro_accum = GyroAccumulator()

    while True:
        if imu.IMURead():
            data = imu.getIMUData()
            if not _fix(data):
                continue
            data['gyro_accum'] = gyro_accum.update(data['timestamp'], data['gyro'])
            yield data
            time.sleep(poll_interval/1000.0)


def _thread_main():
    global LOCK, DATA
    for data in read():
        with LOCK:
            DATA = data.copy()


def start_thread():
    thread = Thread(target=_thread_main)
    thread.daemon = True
    thread.start()
    return thread


if __name__ == '__main__':
    for data in read():
        if data['fusionPoseValid']:
            r, p, y = [math.degrees(v) for v in data['fusionPose']]
            print(f'\rFusion Data: r={r:.2f} p={p:.2f} y={y:.2f}', end='')

