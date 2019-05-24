from auto.capabilities import acquire, release

from car.calibration import (
    _query_motor_params,
    _setup_motors,
    STORE,
    m,
    _choice_input,
)

import itertools
import time


def _find_okay_speed_and_mid_steering(io_device):
    accelerometer = acquire('Accelerometer')
    gyro_accum = acquire('Gyroscope_accum')
    gyro = acquire('Gyroscope')

    f_min_throttle_start, f_max_throttle_start = 1, 35
    r_min_throttle_start, r_max_throttle_start = -1, -35

    speed_target = 1.3   # m/s

    gz_drift_proportional = 10.0

    def test_once(min_throttle, max_throttle):
        m.MOTORS.set_steering(0.0)
        m.MOTORS.set_throttle(0.0)

        _, _, gz_start = gyro_accum.read()

        throttle = (max_throttle + min_throttle) / 2
        speed_est = 0.0
        t_start = time.time()
        t_curr = t_start

        while True:
            m.MOTORS.set_throttle(throttle)
            _, y, _ = accelerometer.read()
            t_prev, t_curr = t_curr, time.time()
            speed_est += (t_curr - t_prev) * y * 9.81
            if abs(speed_est) > speed_target * 1.05:
                break
            if t_curr - t_start >= 1.0:
                break

        _, _, gz_end = gyro_accum.read()
        gz_drift = (gz_end - gz_start) / (t_curr - t_start)

        m.MOTORS.set_throttle(0.0)

        if abs(speed_est) > speed_target:
            max_throttle = throttle
        else:
            min_throttle = throttle

        done = (abs(max_throttle - min_throttle) < 2.0)

        time.sleep(1)   # Give time for the car to stop...

        return throttle, min_throttle, max_throttle, speed_est, done, gz_drift

    def detect_steering_direction(f_throttle, r_throttle):
        def compute_avg_gz(steering_mid):
            STORE.put('CAR_MOTOR_STEERING_MID', steering_mid)
            _setup_motors()
            m.MOTORS.set_steering(0.0)
            m.MOTORS.set_throttle(f_throttle)
            time.sleep(0.05)
            avg_gz = 0.0
            i = 0
            t_start = time.time()
            while time.time() - t_start < 0.3:
                m.MOTORS.set_steering(0.0)
                m.MOTORS.set_throttle(f_throttle)
                _, _, z = gyro.read()
                avg_gz += z
                i += 1
            m.MOTORS.set_throttle(0.0)
            return avg_gz / i

        params = _query_motor_params()
        steering_mid = params['steering_mid']

        results = []

        for offset in [-500, 500, 0]:
            avg_gz = compute_avg_gz(steering_mid + offset)
            time.sleep(0.5)
            m.MOTORS.set_steering(0.0)
            m.MOTORS.set_throttle(r_throttle)
            time.sleep(0.35)
            m.MOTORS.set_throttle(0.0)
            time.sleep(0.5)
            results.append(avg_gz)

        if results[1] > results[0]:
            return 1.0
        else:
            return -1.0

    f_min_throttle, f_max_throttle, f_done = \
        f_min_throttle_start, f_max_throttle_start, False

    r_min_throttle, r_max_throttle, r_done = \
        r_min_throttle_start, r_max_throttle_start, False

    steering_direction = None

    while not f_done or not r_done:

        f_throttle, f_min_throttle, f_max_throttle, f_speed_est, f_done, f_gz_drift = \
            test_once(f_min_throttle, f_max_throttle)
        # print(f_min_throttle, f_max_throttle, f_speed_est, f_done, f_gz_drift)

        r_throttle, r_min_throttle, r_max_throttle, r_speed_est, r_done, r_gz_drift = \
            test_once(r_min_throttle, r_max_throttle)
        # print(r_min_throttle, r_max_throttle, r_speed_est, r_done, r_gz_drift)

        if f_speed_est > 0.1 and r_speed_est < -0.1:
            # This is backwards. Negative y points forward on our cars.
            # So, swap the underlying values.
            # Also, start the binary search over, since the data to now isn't good.
            params = _query_motor_params()
            STORE.put('CAR_MOTOR_THROTTLE_FORWARD', params['throttle_reverse'])
            STORE.put('CAR_MOTOR_THROTTLE_REVERSE', params['throttle_forward'])
            _setup_motors(save=True)
            f_min_throttle, f_max_throttle, f_done = \
                f_min_throttle_start, f_max_throttle_start, False
            r_min_throttle, r_max_throttle, r_done = \
                r_min_throttle_start, r_max_throttle_start, False

        elif f_speed_est < -0.1 and r_speed_est > 0.1:
            # We have some speed, so we can think about steering now.
            if abs(f_gz_drift) > 25.0 or abs(r_gz_drift) > 25.0:
                # Our steering is too far off. Start over the search.
                f_min_throttle, f_max_throttle, f_done = \
                    f_min_throttle_start, f_max_throttle_start, False
                r_min_throttle, r_max_throttle, r_done = \
                    r_min_throttle_start, r_max_throttle_start, False
            if abs(f_gz_drift) > 5.0 or abs(r_gz_drift) > 5.0:
                f_done, r_done = False, False
            if steering_direction is None:
                steering_direction = detect_steering_direction(f_throttle, r_throttle)
            params = _query_motor_params()
            steering_mid = params['steering_mid']
            # print(steering_mid, f_gz_drift, r_gz_drift)
            if abs(f_gz_drift) > abs(r_gz_drift):
                offset = steering_direction * f_gz_drift * gz_drift_proportional
            else:
                offset = steering_direction * -r_gz_drift * gz_drift_proportional
            STORE.put('CAR_MOTOR_STEERING_MID', int(round(steering_mid - offset)))
            _setup_motors()

    f_throttle = (f_min_throttle + f_max_throttle) / 2
    r_throttle = (r_min_throttle + r_max_throttle) / 2

    # print(f_throttle, r_throttle)
    m.CAR_THROTTLE_FORWARD_SAFE_SPEED = f_throttle
    m.CAR_THROTTLE_REVERSE_SAFE_SPEED = r_throttle
    STORE.put('CAR_THROTTLE_FORWARD_SAFE_SPEED', f_throttle)
    STORE.put('CAR_THROTTLE_REVERSE_SAFE_SPEED', r_throttle)
    _setup_motors(save=True)

    release(gyro)
    release(gyro_accum)
    release(accelerometer)

    return steering_direction


def _find_servo_range(steering_direction, io_device):
    params = _query_motor_params()
    steering_mid = params['steering_mid']

    gyro = acquire('Gyroscope')

    def detect_max_steering(f_throttle, r_throttle, db_field, steering_val, start_offset, stride, sign, sign2):
        def compute_avg_gz(test_val):
            STORE.put(db_field, test_val)
            _setup_motors()
            m.MOTORS.set_steering(steering_val)
            m.MOTORS.set_throttle(f_throttle)
            time.sleep(0.2)
            avg_gz = 0.0
            i = 0
            t_start = time.time()
            while time.time() - t_start < 0.4:
                m.MOTORS.set_steering(steering_val)
                m.MOTORS.set_throttle(f_throttle)
                _, _, z = gyro.read()
                avg_gz += z
                i += 1
            m.MOTORS.set_throttle(0.0)
            return avg_gz / i

        prev_gz = None

        for offset in itertools.count(start_offset, stride):
            avg_gz = compute_avg_gz(int(round(steering_mid + offset * sign)))
            time.sleep(0.5)
            m.MOTORS.set_steering(steering_val)
            m.MOTORS.set_throttle(r_throttle)
            time.sleep(0.6)
            m.MOTORS.set_throttle(0.0)
            time.sleep(0.5)
            if prev_gz is not None:
                pct_change = (avg_gz - prev_gz) / prev_gz
                if pct_change * sign2 < 0.05:
                    answer = int(round(steering_mid + (offset - stride) * sign))   # The previous value.
                    STORE.put(db_field, answer)
                    _setup_motors(save=True)
                    break
            prev_gz = avg_gz

        return answer

    f_throttle = m.CAR_THROTTLE_FORWARD_SAFE_SPEED
    r_throttle = m.CAR_THROTTLE_REVERSE_SAFE_SPEED

    steering_left = detect_max_steering(f_throttle, r_throttle, 'CAR_MOTOR_STEERING_LEFT', 45.0, 300, 100, steering_direction, 1.0)
    steering_right = detect_max_steering(f_throttle, r_throttle, 'CAR_MOTOR_STEERING_RIGHT', -45.0, 300, 100, -steering_direction, 1.0)

    release(gyro)


def _hone_speed(io_device):
    f_throttle = m.CAR_THROTTLE_FORWARD_SAFE_SPEED
    r_throttle = m.CAR_THROTTLE_REVERSE_SAFE_SPEED

    gyro_accum = acquire('Gyroscope_accum')

    def compute_avg_gz(throttle, steering, delay):
        m.MOTORS.set_steering(steering)
        m.MOTORS.set_throttle(throttle)
        time.sleep(0.2)   # allow time to change to happen (speed up, slow down, ...)
        _, _, gy_start = gyro_accum.read()
        time.sleep(delay)
        _, _, gy_end = gyro_accum.read()
        return (gy_end - gy_start) / delay

    def find_perfect_throttle(throttle, steering, target_gz):
        m.MOTORS.set_steering(steering)
        m.MOTORS.set_throttle(throttle)
        time.sleep(0.5)   # allow time for car to speed up
        while True:
            gz = compute_avg_gz(throttle, steering, 0.4)
            if throttle < 0:
                gz = -gz
            if abs((gz - target_gz) / target_gz) < 0.05:
                return throttle
            if target_gz > 0 and gz < target_gz or target_gz < 0 and gz > target_gz:
                throttle *= 1.05
            else:
                throttle /= 1.05

    while True:
        if _choice_input(prompt="Will go forward and left. Ready?",
                         choices=['n', 'y'],
                         io_device=io_device) == 'y':
            forward_left_throttle = find_perfect_throttle(f_throttle, 45.0, 120)
            if _choice_input(prompt="Did the car move freely?",
                             choices=['n', 'y'],
                             io_device=io_device) == 'y':
                break

    while True:
        if _choice_input(prompt="Will go forward and right. Ready?",
                         choices=['n', 'y'],
                         io_device=io_device) == 'y':
            forward_right_throttle = find_perfect_throttle(f_throttle, -45.0, -120)
            if _choice_input(prompt="Did the car move freely?",
                             choices=['n', 'y'],
                             io_device=io_device) == 'y':
                break

    while True:
        if _choice_input(prompt="Will go reverse and left. Ready?",
                         choices=['n', 'y'],
                         io_device=io_device) == 'y':
            reverse_left_throttle = find_perfect_throttle(r_throttle, 45.0, 100)
            if _choice_input(prompt="Did the car move freely?",
                             choices=['n', 'y'],
                             io_device=io_device) == 'y':
                break

    while True:
        if _choice_input(prompt="Will go reverse and right. Ready?",
                         choices=['n', 'y'],
                         io_device=io_device) == 'y':
            reverse_right_throttle = find_perfect_throttle(r_throttle, -45.0, -100)
            if _choice_input(prompt="Did the car move freely?",
                             choices=['n', 'y'],
                             io_device=io_device) == 'y':
                break

    f_throttle = (forward_left_throttle + forward_right_throttle) / 2
    r_throttle = (reverse_left_throttle + reverse_right_throttle) / 2

    m.CAR_THROTTLE_FORWARD_SAFE_SPEED = f_throttle
    m.CAR_THROTTLE_REVERSE_SAFE_SPEED = r_throttle
    STORE.put('CAR_THROTTLE_FORWARD_SAFE_SPEED', f_throttle)
    STORE.put('CAR_THROTTLE_REVERSE_SAFE_SPEED', r_throttle)

    release(gyro_accum)


def calibrate(io_device):
    while True:
        if _choice_input(prompt="Will find reasonable speed and center steering. Ready?",
                         choices=['n', 'y'],
                         io_device=io_device) == 'y':
            break

    steering_direction = _find_okay_speed_and_mid_steering(io_device)

    while True:
        if _choice_input(prompt="Will find left and right steering range. Ready?",
                         choices=['n', 'y'],
                         io_device=io_device) == 'y':
            break

    _find_servo_range(steering_direction, io_device)

    while True:
        if _choice_input(prompt="Will hone the forward and reverse speed. Ready?",
                         choices=['n', 'y'],
                         io_device=io_device) == 'y':
            break

    _hone_speed(io_device)


if __name__ == '__main__':
    calibrate('computer')

