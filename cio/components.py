###############################################################################
#
# Copyright (c) 2017-2018 AutoAuto, LLC
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from AutoAuto, LLC.
#
###############################################################################

from .easyi2c import (write_read_i2c_with_integrity,
                      i2c_retry, i2c_poll_until)

from . import N_I2C_TRIES

from .gpiopassthrough import GpioPassthrough, Timer1PWM, Timer3PWM

import struct
import time


def factory_get_controller_version(fd, reg_num):

    class VersionInfo:
        def __init__(self):
            pass

        @i2c_retry(N_I2C_TRIES)
        def version(self):
            """
            Return the major and minor version of the software running on the controller
            as a tuple.
            """
            major, minor = write_read_i2c_with_integrity(fd, [reg_num], 2)
            return major, minor

    return VersionInfo()


def factory_read_battery_millivolts(fd, reg_num):

    class BatteryVoltageReader:
        def __init__(self):
            pass

        @i2c_retry(N_I2C_TRIES)
        def millivolts(self):
            """
            Return the voltage of the battery (in millivolts) connected to the controller.
            Reminder: 1000 millivolts = 1 volt
            """
            lsb, msb = write_read_i2c_with_integrity(fd, [reg_num], 2)
            return (msb << 8) | lsb   # <-- You can also use int.from_bytes(...) but I think doing the bitwise operations explicitely is cooler.

    return BatteryVoltageReader()


def factory_play_buzzer_notes(fd, reg_num):

    class Buzzer:
        def __init__(self):
            pass

        def play(self, notes="o4l16ceg>c8"):
            """
            Tell the controller to play the notes described by the `notes` parameter.
            If the controller is already playing notes, this function will wait for it
            to finish then will play _these_ `notes`. (If the current notes do not finish
            within 10 seconds, this function will give up and raise and error.)
            """
            @i2c_retry(N_I2C_TRIES)
            def is_currently_playing():
                can_play, = write_read_i2c_with_integrity(fd, [reg_num, 0x00], 1)
                return can_play == 0

            @i2c_retry(N_I2C_TRIES)
            def send_new_notes(notes, pos):
                buf = list(notes.encode())
                can_play, = write_read_i2c_with_integrity(fd, [reg_num, 0x01, pos] + buf, 1)
                if can_play != 1:
                    raise Exception("failed to send notes to play")
                return len(buf)

            @i2c_retry(N_I2C_TRIES)
            def start_playback():
                can_play, = write_read_i2c_with_integrity(fd, [reg_num, 0x02], 1)
                if can_play != 1:
                    raise Exception("failed to start playback")

            def chunkify(seq, n):
                """Split `seq` into sublists of size `n`"""
                return [seq[i * n:(i + 1) * n] for i in range((len(seq) + n - 1) // n)]

            i2c_poll_until(is_currently_playing, False, timeout_ms=10000)
            pos = 0
            for chunk in chunkify(notes, 4):
                chunk_len = send_new_notes(chunk, pos)
                pos += chunk_len
            start_playback()

    return Buzzer()


def factory_calibrator(fd, reg_num):

    class Calibrator:
        def __init__(self):
            pass

        @i2c_retry(N_I2C_TRIES)
        def _start_calibration(self):
            status, = write_read_i2c_with_integrity(fd, [reg_num, 0], 1)
            if status != 7:
                raise Exception("Failed to start calibration process.")

        @i2c_retry(N_I2C_TRIES)
        def _check_calibration_status(self):
            status, = write_read_i2c_with_integrity(fd, [reg_num, 1], 1)
            return status

        def calibrate(self):
            """
            Calibrate the Gyroscope and Accelerometer. Don't move the device while the calibration
            is running!
            """
            self._start_calibration()
            print("Calibrating... please wait... this takes about 1 minute.\nDo not move your device while this calibration is running!")
            while True:
                time.sleep(1)
                status = self._check_calibration_status()
                if status == 1:
                    print('.', end='', flush=True)
                elif status == 2:
                    print("\nFinished calibrating!")
                    break
                else:
                    raise Exception("Got unknown status code...")

    return Calibrator()


def factory_read_3axis_floats(fd, reg_num):

    class ThreeAxisFloats:
        def __init__(self):
            pass

        @i2c_retry(N_I2C_TRIES)
        def read(self):
            """
            Read an (x, y, z) tuple-of-floats from one of the controller's components.
            E.g. Read from the Accelerometer, Gyroscope, or Magnetometer.
            """
            buf = write_read_i2c_with_integrity(fd, [reg_num], 3*4)
            return struct.unpack('3f', buf)

    return ThreeAxisFloats()


def factory_read_one_float(fd, reg_num):

    class OneFloat:
        def __init__(self):
            pass

        @i2c_retry(N_I2C_TRIES)
        def read(self):
            """
            Read one floating-point-number from one of the controller's components.
            """
            buf = write_read_i2c_with_integrity(fd, [reg_num], 1*4)
            return struct.unpack('1f', buf)[0]

    return OneFloat()


def factory_push_buttons(fd, reg_num):

    class PushButtons:
        def __init__(self):
            pass

        @i2c_retry(N_I2C_TRIES)
        def num_buttons(self):
            """
            Return the number of buttons on the device.
            """
            n, = write_read_i2c_with_integrity(fd, [reg_num, 0x00], 1)
            return n

        @i2c_retry(N_I2C_TRIES)
        def button_state(self, button_index):
            """
            Return the state of the button at the given index (zero-based).
            Returns a tuple of (num_presses, num_releases, is_currently_pressed)
            which are of types (int, int, bool).
            """
            buf = write_read_i2c_with_integrity(fd, [reg_num, 0x01+button_index], 3)
            presses = int(buf[0])
            releases = int(buf[1])
            is_pressed = bool(buf[2])
            return presses, releases, is_pressed

        @i2c_retry(N_I2C_TRIES)
        def debug(self):
            """
            Print debug info.
            """
            buf = write_read_i2c_with_integrity(fd, [reg_num, 0xFF], 6)
            official_state = int(buf[0])
            unofficial_state = int(buf[1])
            debug_value = struct.unpack('1I', buf[2:])[0]
            return official_state, unofficial_state, debug_value

    return PushButtons()


def factory_leds(fd, reg_num):

    class LEDs:
        def __init__(self):
            pass

        @i2c_retry(N_I2C_TRIES)
        def set_values(self, red=False, green=False, blue=False):
            """
            Set the LED on/off value for each of the three LEDs.
            """
            led_state = ((1 if red else 0) | ((1 if green else 0) << 1) | ((1 if blue else 0) << 2))
            status, = write_read_i2c_with_integrity(fd, [reg_num, 0x00, led_state], 1)
            if status != 72:
                raise Exception("failed to set LED state")

        @i2c_retry(N_I2C_TRIES)
        def set_mode(self, mode):
            """
            Set the `mode` of the LEDs. There is currently only two modes:
             - 0: manual mode (you use `set_values()` (the default)
             - 1: spinning mode (the LEDs flash red, then green, then blue, then repeat)
            """
            status, = write_read_i2c_with_integrity(fd, [reg_num, 0x01, mode], 1)
            if status != 72:
                raise Exception("failed to set LED mode")

    return LEDs()


def factory_photoresistor(fd, reg_num):

    class Photoresistor:
        def __init__(self):
            pass

        @i2c_retry(N_I2C_TRIES)
        def read(self):
            """
            Read the voltage of the photoresistor pin, and read
            the computed resistance of the photoresistor.
            """
            buf = write_read_i2c_with_integrity(fd, [reg_num], 8)
            millivolts, resistance = struct.unpack('2I', buf)
            return millivolts, resistance

        def read_millivolts(self):
            """
            Read the raw voltage of the photoresistor pin.
            """
            millivolts, resistance = self.read()
            return millivolts

        def read_ohms(self):
            """
            Read the resistance of the photoresistor (in ohms). The photoresistor's
            resistance changes depending on how much light is on it, thus the name!
            """
            millivolts, resistance = self.read()
            return resistance

    return Photoresistor()


def factory_read_encoders(fd, reg_num):

    class Encoders:
        def __init__(self):
            pass

        @i2c_retry(N_I2C_TRIES)
        def enable_e1(self):
            """
            Enable the first encoder pair.
            """
            status, = write_read_i2c_with_integrity(fd, [reg_num, 0x00], 1)
            if status != 31:
                raise Exception("Failed to enable encoder")

        @i2c_retry(N_I2C_TRIES)
        def enable_e2(self):
            """
            Enable the second encoder pair.
            """
            status, = write_read_i2c_with_integrity(fd, [reg_num, 0x01], 1)
            if status != 31:
                raise Exception("Failed to enable encoder")

        @i2c_retry(N_I2C_TRIES)
        def disable_e1(self):
            """
            Disable the first encoder pair.
            """
            status, = write_read_i2c_with_integrity(fd, [reg_num, 0x02], 1)
            if status != 31:
                raise Exception("Failed to disable encoder")

        @i2c_retry(N_I2C_TRIES)
        def disable_e2(self):
            """
            Disable the second encoder pair.
            """
            status, = write_read_i2c_with_integrity(fd, [reg_num, 0x03], 1)
            if status != 31:
                raise Exception("Failed to disable encoder")

        @i2c_retry(N_I2C_TRIES)
        def read_e1_counts(self):
            """
            Return the state of the first encoder (e1). Three values are returned:
             - Number of "clicks"
             - Pin A change count.
             - Pin B change count.
            """
            buf = write_read_i2c_with_integrity(fd, [reg_num, 0x04], 6)
            return struct.unpack('3h', buf)

        @i2c_retry(N_I2C_TRIES)
        def read_e1_timing(self):
            """
            Return the number of microseconds that the encoder pin was high. This
            can be used to read a PWM signal (assuming the PWM signal has a known,
            fixed frequency). If the pin has not gone high-then-low recently (within
            the last half-second), the value returned here will be 0 to indicate
            it is not presently known (i.e. the PWM signal is not currently coming
            through). Two values are returned by this method: `(pin_a_usecs, pin_b_usecs)`.
            Recall: 1000000 microseconds = 1 second
            """
            buf = write_read_i2c_with_integrity(fd, [reg_num, 0x05], 8)
            return struct.unpack('2I', buf)

        @i2c_retry(N_I2C_TRIES)
        def read_e2_counts(self):
            """
            Same as `read_e1_counts()`, but for the second encoder (e2).
            """
            buf = write_read_i2c_with_integrity(fd, [reg_num, 0x06], 6)
            return struct.unpack('3h', buf)

        @i2c_retry(N_I2C_TRIES)
        def read_e2_timing(self):
            """
            Same as `read_e1_timing()`, but for the second encoder (e2).
            """
            buf = write_read_i2c_with_integrity(fd, [reg_num, 0x07], 8)
            return struct.unpack('2I', buf)

    return Encoders()


def factory_get_loop_frequency(fd, reg_num):

    class LoopFrequency:
        def __init__(self):
            pass

        @i2c_retry(N_I2C_TRIES)
        def read(self):
            """
            Returns the loop frequency of the microcontroller (in Hz).
            """
            buf = write_read_i2c_with_integrity(fd, [reg_num], 4)
            return struct.unpack('1I', buf)[0]

    return LoopFrequency()


def factory_set_car_motors(fd, reg_num):

    class CarMotors:
        def __init__(self):
            pass

        @i2c_retry(N_I2C_TRIES)
        def on(self):
            """
            Tell the car to begin controlling the motors (the main motor and the servo).
            The car will use the most recently set PWM signal parameters, or it will
            read from its EEPROM to get those values.
            """
            status, = write_read_i2c_with_integrity(fd, [reg_num, 0x00], 1)
            if status != 104:
                raise Exception("failed to turn on car motors")

        @i2c_retry(N_I2C_TRIES)
        def set_steering(self, steering):
            """
            Set the car's steering (i.e. move the servo).

            Pass a value in the range [-45, 45] to represent [full-right, full-left].
            """
            steering = int(round(min(max(steering, -45), 45)))
            status, = write_read_i2c_with_integrity(fd, [reg_num, 0x01, (steering & 0xFF), ((steering >> 8) & 0xFF)], 1)
            if status != 104:
                raise Exception("failed to set steering")

        @i2c_retry(N_I2C_TRIES)
        def set_throttle(self, throttle):
            """
            Set the car's throttle (i.e. power send to the main motor).

            Pass a value in the range [-100, 100] to represent [full-reverse, full-forward].
            """
            throttle = int(round(min(max(throttle, -100), 100)))
            status, = write_read_i2c_with_integrity(fd, [reg_num, 0x02, (throttle & 0xFF), ((throttle >> 8) & 0xFF)], 1)
            if status != 104:
                raise Exception("failed to set throttle")

        @i2c_retry(N_I2C_TRIES)
        def off(self):
            """
            Turn off the car's PWM motor control.
            """
            status, = write_read_i2c_with_integrity(fd, [reg_num, 0x03], 1)
            if status != 104:
                raise Exception("failed to turn off car motors")

        def set_params(self, top, steering_left, steering_mid, steering_right, steering_millis,
                             throttle_forward, throttle_mid, throttle_reverse, throttle_millis):
            """
            Set the car motors' PWM signal parameters.
            """
            @i2c_retry(N_I2C_TRIES)
            def set_top():
                payload = list(struct.pack("1H", top))
                status, = write_read_i2c_with_integrity(fd, [reg_num, 0x04] + payload, 1)
                if status != 104:
                    raise Exception("failed to set params: top")

            @i2c_retry(N_I2C_TRIES)
            def set_steering_params():
                payload = list(struct.pack("4H", steering_left, steering_mid, steering_right, steering_millis))
                status, = write_read_i2c_with_integrity(fd, [reg_num, 0x05] + payload, 1)
                if status != 104:
                    raise Exception("failed to set params: steering_left, steering_mid, steering_right, steering_millis")

            @i2c_retry(N_I2C_TRIES)
            def set_throttle_params():
                payload = list(struct.pack("4H", throttle_forward, throttle_mid, throttle_reverse, throttle_millis))
                status, = write_read_i2c_with_integrity(fd, [reg_num, 0x06] + payload, 1)
                if status != 104:
                    raise Exception("failed to set params: throttle_forward, throttle_mid, throttle_reverse, throttle_millis")

            set_top()
            set_steering_params()
            set_throttle_params()

        def save_params(self):
            """
            Save the car motors' current parameters to the EEPROM.
            """
            @i2c_retry(N_I2C_TRIES)
            def save():
                status, = write_read_i2c_with_integrity(fd, [reg_num, 0x07], 1)
                if status != 104:
                    raise Exception("failed to tell car to save motor params")

            @i2c_retry(N_I2C_TRIES)
            def is_saved():
                status, = write_read_i2c_with_integrity(fd, [reg_num, 0x08], 1)
                return status == 0

            save()
            i2c_poll_until(is_saved, True, timeout_ms=1000)

    return CarMotors()


def factory_pid(fd, reg_num):

    class PID:
        """
        The microcontroller has a very simple PID algorithm that can be tuned.
        """
        def __init__(self):
            pass

        @i2c_retry(N_I2C_TRIES)
        def disable(self):
            """
            Disable the PID controller (i.e. stop driving the actuator).
            """
            status, = write_read_i2c_with_integrity(fd, [reg_num, 0x00], 1)
            if status != 52:
                raise Exception("failed to disable PID loop")

        def set_pid(self, p, i, d, error_accum_max=0.0):
            """
            Sets P, I, and D.

            `error_accum_max` is the max accumulated error that will be accumulated.
            This is a common thing that is done to tame the PID loop and not crazy overshoot
            due to `I` accumulating unreasonably high. Zero means there is no limit.
            """
            @i2c_retry(N_I2C_TRIES)
            def set_val(instruction, val):
                payload = list(struct.pack("1f", val))
                status, = write_read_i2c_with_integrity(fd, [reg_num, instruction] + payload, 1)
                if status != 52:
                    raise Exception("failed to set PID value for instruction {}".format(instruction))

            set_val(0x01, p)
            set_val(0x02, i)
            set_val(0x03, d)
            set_val(0x04, error_accum_max)

        def save_pid(self):
            """
            Save P, I, D (and `error_accum_max`) to the EEPROM.
            """
            @i2c_retry(N_I2C_TRIES)
            def save():
                status, = write_read_i2c_with_integrity(fd, [reg_num, 0x05], 1)
                if status != 52:
                    raise Exception("failed to save PID params")

            @i2c_retry(N_I2C_TRIES)
            def is_saved():
                status, = write_read_i2c_with_integrity(fd, [reg_num, 0x06], 1)
                return status == 0

            save()
            i2c_poll_until(is_saved, True, timeout_ms=1000)

        @i2c_retry(N_I2C_TRIES)
        def set_point(self, point):
            """
            Set the sensor's "set point". The actuator will be controlled so that
            the sensor stays in the "set point".
            """
            status, = write_read_i2c_with_integrity(fd, [reg_num, 0x07] + list(struct.pack("1f", point)), 1)
            if status != 52:
                raise Exception("failed to set the PID \"set point\"")

        @i2c_retry(N_I2C_TRIES)
        def enable(self, invert_output=False):
            """
            Enable the PID controller (i.e. begin to drive the actuator).
            """
            status, = write_read_i2c_with_integrity(fd, [reg_num, 0x08, (0x01 if invert_output else 0x00)], 1)
            if status != 52:
                raise Exception("failed to enable PID loop")

        def debug(self):
            """
            Return the internal values of the PID algorithm for debugging purposes.
            """
            @i2c_retry(N_I2C_TRIES)
            def read_one_float(index):
                float_buf = write_read_i2c_with_integrity(fd, [reg_num, index], 4)
                return struct.unpack('1f', float_buf)[0]

            return {
                'delta_seconds': read_one_float(0x09),
                'curr_value': read_one_float(0x0a),
                'curr_error': read_one_float(0x0b),
                'm_error_accum': read_one_float(0x0c),
                'm_last_error': read_one_float(0x0d),
                'error_diff': read_one_float(0x0e),
                'p_part': read_one_float(0x0f),
                'i_part': read_one_float(0x10),
                'd_part': read_one_float(0x11),
                'output': read_one_float(0x12),
            }

    return PID()


KNOWN_COMPONENTS = {
    'VersionInfo':           factory_get_controller_version,
    'BatteryVoltageReader':  factory_read_battery_millivolts,
    'Buzzer':                factory_play_buzzer_notes,
    'Calibrator':            factory_calibrator,
    'Accelerometer':         factory_read_3axis_floats,
    'Gyroscope':             factory_read_3axis_floats,
    'Gyroscope_accum':       factory_read_3axis_floats,
    'Magnetometer':          factory_read_3axis_floats,
    'Temperature':           factory_read_one_float,
    'PushButtons':           factory_push_buttons,
    'LEDs':                  factory_leds,
    'Photoresistor':         factory_photoresistor,
    'Barometer':             factory_read_one_float,
    'Encoders':              factory_read_encoders,
    'LoopFrequency':         factory_get_loop_frequency,
    'CarMotors':             factory_set_car_motors,
    'PID_steering':          factory_pid,
    'GpioPassthrough':       GpioPassthrough,
    'Timer1PWM':             Timer1PWM,
    'Timer3PWM':             Timer3PWM,
}

