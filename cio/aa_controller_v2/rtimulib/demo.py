import RTIMU
import os
import sys
import math
import time

CURR_DIR = os.path.dirname(os.path.realpath(__file__))


def demo():
    settings = RTIMU.Settings(os.path.join(CURR_DIR, 'RTIMULib'))

    imu = RTIMU.RTIMU(settings)

    print('IMU Name:', imu.IMUName())
    print('IMU Type:', imu.IMUType())

    if not imu.IMUInit():
        print('IMU Init Failed')
        sys.exit(1)
    else:
        print('IMU Init Succeeded')

    imu.setSlerpPower(0.02)
    imu.setGyroEnable(True)
    imu.setAccelEnable(True)
    imu.setCompassEnable(False)

    poll_interval = imu.IMUGetPollInterval()

    print(f'Recommended Poll Interval: {poll_interval}mS')

    def print_all(data):
        print(data['timestamp'])
        pairs = [
            ('fusionPoseValid', 'fusionPose'),
            ('fusionQPoseValid', 'fusionQPose'),
            ('gyroValid', 'gyro'),
            ('accelValid', 'accel'),
            ('compassValid', 'compass'),
            ('pressureValid', 'pressure'),
            ('temperatureValid', 'temperature'),
            ('humidityValid', 'humidity'),
        ]
        for a, b in pairs:
            if data[a]:
                print(f'{b:20}: {data[b]}')

    def print_rpy(data):
        if data['fusionPoseValid']:
            t = data['timestamp']
            r, p, y = [math.degrees(v) for v in data['fusionPose']]
            print(f'\r{t} Fusion Data: r={r:.2f} p={p:.2f} y={y:.2f}', end='')

    n = 0
    then = time.time()

    while True:
        if imu.IMURead():
            data = imu.getIMUData()
            #print_all(data)
            print_rpy(data)
            n += 1
            now = time.time()
            if (now - then) >= 1.0:
                print('\nLoop frequency:', n)
                n = 0
                then = now
            time.sleep(poll_interval/1000.0)


if __name__ == '__main__':
    demo()

