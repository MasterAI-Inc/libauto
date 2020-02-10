###############################################################################
#
# Copyright (c) 2017-2020 Master AI, Inc.
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from Master AI, Inc.
#
###############################################################################

from .easyi2c import (write_read_i2c_with_integrity,
                      i2c_retry, i2c_poll_until)

from . import N_I2C_TRIES

from .timers import Timer1PWM, Timer3PWM

from .db import default_db
from .battery_discharge_curve import battery_map_millivolts_to_percentage

import cio

import struct
import asyncio
from math import floor
from collections import deque


class VersionInfo(cio.VersionInfoIface):
    def __init__(self, fd, reg_num):
        self.fd = fd
        self.reg_num = reg_num

    async def name(self):
        return "AutoAuto v2 Controller"

    @i2c_retry(N_I2C_TRIES)
    async def version(self):
        major, minor = await write_read_i2c_with_integrity(self.fd, [self.reg_num], 2)
        return major, minor


class Credentials(cio.CredentialsIface):
    def __init__(self, fd, reg_num):
        self.fd = fd
        self.reg_num = reg_num
        self.db = None
        self.loop = asyncio.get_running_loop()

    async def get_labs_auth_code(self):
        return await self.loop.run_in_executor(None, self._get_labs_auth_code)

    async def set_labs_auth_code(self, auth_code):
        if (await self.get_labs_auth_code()) is None:
            await self.loop.run_in_executor(None, self._set_labs_auth_code, auth_code)
            return True
        return False

    async def get_jupyter_password(self):
        return await self.loop.run_in_executor(None, self._get_jupyter_password)

    async def set_jupyter_password(self, password):
        if (await self.get_jupyter_password()) is None:
            await self.loop.run_in_executor(None, self._set_jupyter_password, password)
            return True
        return False

    def _get_db(self):
        if self.db is None:
            self.db = default_db()
        return self.db

    def _get_labs_auth_code(self):
        return self._get_db().get('DEVICE_LABS_AUTH_CODE', None)

    def _set_labs_auth_code(self, auth_code):
        self._get_db().put('DEVICE_LABS_AUTH_CODE', auth_code)

    def _get_jupyter_password(self):
        return self._get_db().get('DEVICE_JUPYTER_PASSWORD', None)

    def _set_jupyter_password(self, password):
        self._get_db().put('DEVICE_JUPYTER_PASSWORD', password)


class LoopFrequency(cio.LoopFrequencyIface):
    def __init__(self, fd, reg_num):
        self.fd = fd
        self.reg_num = reg_num

    @i2c_retry(N_I2C_TRIES)
    async def read(self):
        buf = await write_read_i2c_with_integrity(self.fd, [self.reg_num], 4)
        return struct.unpack('1I', buf)[0]


class BatteryVoltageReader(cio.BatteryVoltageReaderIface):
    def __init__(self, fd, reg_num):
        self.fd = fd
        self.reg_num = reg_num

    @i2c_retry(N_I2C_TRIES)
    async def millivolts(self):
        lsb, msb = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x00], 2)
        return (msb << 8) | lsb   # <-- You can also use int.from_bytes(...) but I think doing the bitwise operations explicitly is cooler.

    async def estimate_remaining(self, millivolts=None):
        if millivolts is None:
            millivolts = await self.millivolts()
        percentage = battery_map_millivolts_to_percentage(millivolts)
        minutes = 4.0 * 60.0 * (percentage / 100.0)  # Assumes the full battery lasts 4 hours.
        return floor(minutes), floor(percentage)

    async def should_shut_down(self):
        on_flag, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x01], 1)
        return not on_flag


class Buzzer(cio.BuzzerIface):
    def __init__(self, fd, reg_num):
        self.fd = fd
        self.reg_num = reg_num

    @i2c_retry(N_I2C_TRIES)
    async def is_currently_playing(self):
        can_play, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x00], 1)
        return can_play == 0

    async def wait(self):
        await i2c_poll_until(self.is_currently_playing, False, timeout_ms=100000)

    async def play(self, notes="o4l16ceg>c8"):
        notes = notes.replace(' ', '')  # remove spaces from the notes (they don't hurt, but they take up space and the microcontroller doesn't have a ton of space)

        @i2c_retry(N_I2C_TRIES)
        async def send_new_notes(notes, pos):
            buf = list(notes.encode())
            can_play, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x01, pos] + buf, 1)
            if can_play != 1:
                raise Exception("failed to send notes to play")
            return len(buf)

        @i2c_retry(N_I2C_TRIES)
        async def start_playback():
            can_play, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x02], 1)
            # Ignore return value. Why? Because this call commonly requires multiple retries
            # (as done by `i2c_retry`) thus if we retry, then the playback will have already
            # started and we'll be (wrongly) informed that it cannot start (because it already
            # started!). Thus, the check below has been disabled:
            #
            #if can_play != 1:
            #    raise Exception("failed to start playback")

        def chunkify(seq, n):
            """Split `seq` into sublists of size `n`"""
            return [seq[i * n:(i + 1) * n] for i in range((len(seq) + n - 1) // n)]

        await self.wait()

        pos = 0
        for chunk in chunkify(notes, 4):
            chunk_len = await send_new_notes(chunk, pos)
            pos += chunk_len

        await start_playback()


class Gyroscope(cio.GyroscopeIface):
    def __init__(self, fd, reg_num):
        self.fd = fd
        self.reg_num = reg_num

    @i2c_retry(N_I2C_TRIES)
    async def read(self):
        buf = await write_read_i2c_with_integrity(self.fd, [self.reg_num], 3*4)
        x, y, z = struct.unpack('3f', buf)
        x, y = -x, -y    # rotate 180 degrees around z
        return x, y, z


class GyroscopeAccum(cio.GyroscopeAccumIface):
    def __init__(self, fd, reg_num):
        self.fd = fd
        self.reg_num = reg_num
        self.x_off = 0.0
        self.y_off = 0.0
        self.z_off = 0.0

    async def reset(self):
        x, y, z = await self._read_raw()
        self.x_off = x
        self.y_off = y
        self.z_off = z

    async def read(self):
        x, y, z = await self._read_raw()
        return (x - self.x_off), (y - self.y_off), (z - self.z_off)

    @i2c_retry(N_I2C_TRIES)
    async def _read_raw(self):
        buf = await write_read_i2c_with_integrity(self.fd, [self.reg_num], 3*4)
        x, y, z = struct.unpack('3f', buf)
        x, y = -x, -y    # rotate 180 degrees around z
        return x, y, z


class Accelerometer(cio.AccelerometerIface):
    def __init__(self, fd, reg_num):
        self.fd = fd
        self.reg_num = reg_num

    @i2c_retry(N_I2C_TRIES)
    async def read(self):
        buf = await write_read_i2c_with_integrity(self.fd, [self.reg_num], 3*4)
        x, y, z = struct.unpack('3f', buf)
        x, y = -x, -y    # rotate 180 degrees around z
        return x, y, z


class PushButtons(cio.PushButtonsIface):
    def __init__(self, fd, reg_num):
        self.fd = fd
        self.reg_num = reg_num
        self.n = None
        self.states = None
        self.event_queue = deque()

    @i2c_retry(N_I2C_TRIES)
    async def num_buttons(self):
        n, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x00], 1)
        return n

    @i2c_retry(N_I2C_TRIES)
    async def button_state(self, button_index):
        buf = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x01+button_index], 3)
        presses = int(buf[0])
        releases = int(buf[1])
        is_pressed = bool(buf[2])
        return presses, releases, is_pressed

    async def get_events(self):
        if self.n is None:
            self.n = await self.num_buttons()
            self.states = [await self.button_state(i) for i in range(self.n)]
            return []

        events = []

        for prev_state, i in zip(self.states, range(self.n)):
            state = await self.button_state(i)
            if state == prev_state:
                continue

            diff_presses  = (state[0] - prev_state[0]) % 256
            diff_releases = (state[1] - prev_state[1]) % 256

            if diff_presses == 0 and diff_releases == 0:
                continue

            if prev_state[2]:  # if button **was** pressed
                # We'll add `released` events first.
                while diff_presses > 0 or diff_releases > 0:
                    if diff_releases > 0:
                        events.append({'button': i, 'action': 'released'})
                        diff_releases -= 1
                    if diff_presses > 0:
                        events.append({'button': i, 'action': 'pressed'})
                        diff_presses -= 1
            else:
                # We'll add `pressed` events first.
                while diff_presses > 0 or diff_releases > 0:
                    if diff_presses > 0:
                        events.append({'button': i, 'action': 'pressed'})
                        diff_presses -= 1
                    if diff_releases > 0:
                        events.append({'button': i, 'action': 'released'})
                        diff_releases -= 1

            self.states[i] = state

        return events

    async def wait_for_event(self):
        if not self.event_queue:   # if empty
            while True:
                events = await self.get_events()
                if events:  # if not empty
                    self.event_queue.extend(events)
                    return self.event_queue.popleft()
                await asyncio.sleep(0.05)
        else:
            return self.event_queue.popleft()

    async def wait_for_action(self, action='pressed'):
        while True:
            event = await self.wait_for_event()
            if action == 'any' or action == event['action']:
                return event['button'], event['action']


class LEDs(cio.LEDsIface):
    def __init__(self, fd, reg_num):
        self.fd = fd
        self.reg_num = reg_num
        self.vals = {
            'red': False,
            'green': False,
            'blue': False,
        }

    async def led_map(self):
        return {
            'red': 'The red LED',
            'green': 'The green LED',
            'blue': 'The blue LED',
        }

    @i2c_retry(N_I2C_TRIES)
    async def _set(self):
        red   = self.vals['red']
        green = self.vals['green']
        blue  = self.vals['blue']
        led_state = ((1 if red else 0) | ((1 if green else 0) << 1) | ((1 if blue else 0) << 2))
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x00, led_state], 1)
        if status != 72:
            raise Exception("failed to set LED state")

    async def set_led(self, led_identifier, val):
        self.vals[led_identifier] = val
        await self._set()

    async def set_many_leds(self, id_val_list):
        for led_identifier, val in id_val_list:
            self.vals[led_identifier] = val
        await self._set()

    async def mode_map(self):
        return {
            'spin': 'the LEDs flash red, then green, then blue, then repeat',
        }

    @i2c_retry(N_I2C_TRIES)
    async def set_mode(self, mode_identifier):
        mode = 0   # default mode where the values are merely those set by `set_led()`
        if mode_identifier == 'spin':
            mode = 1
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x01, mode], 1)
        if status != 72:
            raise Exception("failed to set LED mode")


class Photoresistor(cio.PhotoresistorIface):
    def __init__(self, fd, reg_num):
        self.fd = fd
        self.reg_num = reg_num

    @i2c_retry(N_I2C_TRIES)
    async def read(self):
        buf = await write_read_i2c_with_integrity(self.fd, [self.reg_num], 8)
        millivolts, resistance = struct.unpack('2I', buf)
        return millivolts, resistance

    async def read_millivolts(self):
        millivolts, resistance = await self.read()
        return millivolts

    async def read_ohms(self):
        millivolts, resistance = await self.read()
        return resistance


class Encoders(cio.EncodersIface):
    def __init__(self, fd, reg_num):
        self.fd = fd
        self.reg_num = reg_num

    async def num_encoders(self):
        return 2

    async def enable(self, encoder_index):
        if encoder_index == 0:
            return await self._enable_e1()
        else:
            return await self._enable_e2()

    async def read_counts(self, encoder_index):
        if encoder_index == 0:
            return await self._read_e1_counts()
        else:
            return await self._read_e2_counts()

    async def read_timing(self, encoder_index):
        if encoder_index == 0:
            return await self._read_e1_timing()
        else:
            return await self._read_e2_timing()

    async def disable(self, encoder_index):
        if encoder_index == 0:
            return await self._disable_e1()
        else:
            return await self._disable_e2()

    @i2c_retry(N_I2C_TRIES)
    async def _enable_e1(self):
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x00], 1)
        if status != 31:
            raise Exception("Failed to enable encoder")

    @i2c_retry(N_I2C_TRIES)
    async def _enable_e2(self):
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x01], 1)
        if status != 31:
            raise Exception("Failed to enable encoder")

    @i2c_retry(N_I2C_TRIES)
    async def _disable_e1(self):
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x02], 1)
        if status != 31:
            raise Exception("Failed to disable encoder")

    @i2c_retry(N_I2C_TRIES)
    async def _disable_e2(self):
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x03], 1)
        if status != 31:
            raise Exception("Failed to disable encoder")

    @i2c_retry(N_I2C_TRIES)
    async def _read_e1_counts(self):
        buf = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x04], 6)
        return struct.unpack('3h', buf)

    @i2c_retry(N_I2C_TRIES)
    async def _read_e1_timing(self):
        buf = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x05], 8)
        return struct.unpack('2I', buf)

    @i2c_retry(N_I2C_TRIES)
    async def _read_e2_counts(self):
        buf = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x06], 6)
        return struct.unpack('3h', buf)

    @i2c_retry(N_I2C_TRIES)
    async def _read_e2_timing(self):
        buf = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x07], 8)
        return struct.unpack('2I', buf)


class CarMotors(cio.CarMotorsIface):
    def __init__(self, fd, reg_num):
        self.fd = fd
        self.reg_num = reg_num
        self.db = None
        self.loop = asyncio.get_running_loop()

    @i2c_retry(N_I2C_TRIES)
    async def on(self):
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x00], 1)
        if status != 104:
            raise Exception("failed to turn on car motors")

    @i2c_retry(N_I2C_TRIES)
    async def set_steering(self, steering):
        steering = int(round(min(max(steering, -45), 45)))
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x01, (steering & 0xFF), ((steering >> 8) & 0xFF)], 1)
        if status != 104:
            raise Exception("failed to set steering")

    @i2c_retry(N_I2C_TRIES)
    async def set_throttle(self, throttle):
        throttle = int(round(min(max(throttle, -100), 100)))
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x02, (throttle & 0xFF), ((throttle >> 8) & 0xFF)], 1)
        if status != 104:
            raise Exception("failed to set throttle")

    def _get_db(self):
        if self.db is None:
            self.db = default_db()
        return self.db

    def _get_safe_throttle(self):
        db = self._get_db()
        min_throttle = db.get('CAR_THROTTLE_FORWARD_SAFE_SPEED', -22)
        max_throttle = db.get('CAR_THROTTLE_REVERSE_SAFE_SPEED', 23)
        return min_throttle, max_throttle

    def _set_safe_throttle(self, min_throttle, max_throttle):
        db = self._get_db()
        db.put('CAR_THROTTLE_FORWARD_SAFE_SPEED', min_throttle)
        db.put('CAR_THROTTLE_REVERSE_SAFE_SPEED', max_throttle)

    async def get_safe_throttle(self):
        return await self.loop.run_in_executor(None, self._get_safe_throttle)

    async def set_safe_throttle(self, min_throttle, max_throttle):
        return await self.loop.run_in_executor(None, self._set_safe_throttle, min_throttle, max_throttle)

    @i2c_retry(N_I2C_TRIES)
    async def off(self):
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x03], 1)
        if status != 104:
            raise Exception("failed to turn off car motors")

    async def set_params(self, top, steering_left, steering_mid, steering_right, steering_millis,
                         throttle_forward, throttle_mid, throttle_reverse, throttle_millis):
        """
        Set the car motors' PWM signal parameters.
        This is a non-standard method which is not a part of the CarMotors interface.
        """
        @i2c_retry(N_I2C_TRIES)
        async def set_top():
            payload = list(struct.pack("1H", top))
            status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x04] + payload, 1)
            if status != 104:
                raise Exception("failed to set params: top")

        @i2c_retry(N_I2C_TRIES)
        async def set_steering_params():
            payload = list(struct.pack("4H", steering_left, steering_mid, steering_right, steering_millis))
            status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x05] + payload, 1)
            if status != 104:
                raise Exception("failed to set params: steering_left, steering_mid, steering_right, steering_millis")

        @i2c_retry(N_I2C_TRIES)
        async def set_throttle_params():
            payload = list(struct.pack("4H", throttle_forward, throttle_mid, throttle_reverse, throttle_millis))
            status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x06] + payload, 1)
            if status != 104:
                raise Exception("failed to set params: throttle_forward, throttle_mid, throttle_reverse, throttle_millis")

        await set_top()
        await set_steering_params()
        await set_throttle_params()

    async def save_params(self):
        """
        Save the car motors' current parameters to the EEPROM.
        This is a non-standard method which is not a part of the CarMotors interface.
        """
        @i2c_retry(N_I2C_TRIES)
        async def save():
            status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x07], 1)
            if status != 104:
                raise Exception("failed to tell car to save motor params")

        @i2c_retry(N_I2C_TRIES)
        async def is_saved():
            status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x08], 1)
            return status == 0

        await save()
        await i2c_poll_until(is_saved, True, timeout_ms=1000)

    def rpc_extra_exports(self):
        return ['set_params', 'save_params']


class PWMs(cio.PWMsIface):
    def __init__(self, fd, reg_num):
        self.fd = fd
        self.t1_reg_num = reg_num[0]
        self.t3_reg_num = reg_num[1]
        self.timer_1 = Timer1PWM(self.fd, self.t1_reg_num)
        self.timer_3 = Timer3PWM(self.fd, self.t3_reg_num)
        self.enabled = {}   # dict mapping pin_index to frequency

    async def num_pins(self):
        return 4

    async def enable(self, pin_index, frequency, duty=0):
        if 2000000 % frequency:
            raise Exception('cannot set frequency exactly')
        top = 2000000 // frequency

        duty = min(100.0, duty)
        duty = max(0.0, duty)
        duty = int(round(duty / 100.0 * top))

        if pin_index in (0, 1, 2):
            # These pins are on Timer 1.
            needs_init = True

            for idx in (0, 1, 2):
                if idx in self.enabled:
                    if frequency != self.enabled[idx]:
                        raise Exception("All enabled pins 0, 1, and 2 must have the same frequency.")
                    needs_init = False

            if needs_init:
                await self.timer_1.set_top(top)

            if pin_index == 0:
                await self.timer_1.set_ocr_a(duty)
                await self.timer_1.enable_a()
            elif pin_index == 1:
                await self.timer_1.set_ocr_b(duty)
                await self.timer_1.enable_b()
            elif pin_index == 2:
                await self.timer_1.set_ocr_c(duty)
                await self.timer_1.enable_c()

        elif pin_index == 3:
            # This pin is on Timer 3.
            await self.timer_3.set_top(top)
            await self.timer_3.set_ocr(duty)
            await self.timer_3.enable()

        else:
            raise Exception('invalid pin_index')

        self.enabled[pin_index] = frequency

    async def set_duty(self, pin_index, duty):
        if pin_index not in self.enabled:
            raise Exception('that pin is not enabled')

        frequency = self.enabled[pin_index]
        top = 2000000 // frequency

        duty = min(100.0, duty)
        duty = max(0.0, duty)
        duty = int(round(duty / 100.0 * top))

        if pin_index == 0:
            await self.timer_1.set_ocr_a(duty)
        elif pin_index == 1:
            await self.timer_1.set_ocr_b(duty)
        elif pin_index == 2:
            await self.timer_1.set_ocr_c(duty)
        elif pin_index == 3:
            await self.timer_3.set_ocr(duty)

    async def disable(self, pin_index):
        if pin_index not in self.enabled:
            raise Exception('that pin is not enabled')

        if pin_index == 0:
            await self.timer_1.disable_a()
        elif pin_index == 1:
            await self.timer_1.disable_b()
        elif pin_index == 2:
            await self.timer_1.disable_c()
        elif pin_index == 3:
            await self.timer_3.disable()

        del self.enabled[pin_index]


class Calibrator(cio.CalibratorIface):
    def __init__(self, fd, reg_num):
        self.fd = fd
        self.reg_num = reg_num

    @i2c_retry(N_I2C_TRIES)
    async def start(self):
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0], 1)
        if status != 7:
            raise Exception("Failed to start calibration process.")

    @i2c_retry(N_I2C_TRIES)
    async def status(self):
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 1], 1)
        # Status 0 means not started, 1 means currently calibrating, 2 means done calibrating
        if status == 0 or status == 1:
            return status
        elif status == 2:
            return -1  # <-- conform to CIO interface
        else:
            raise Exception("Unknown calibration status")

    async def script_name(self):
        return "calibrate_car_v2"


class PidSteering(cio.PidSteeringIface):
    def __init__(self, fd, reg_num):
        self.fd = fd
        self.reg_num = reg_num

    async def set_pid(self, p, i, d, error_accum_max=0.0, save=False):
        @i2c_retry(N_I2C_TRIES)
        async def set_val(instruction, val):
            payload = list(struct.pack("1f", val))
            status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, instruction] + payload, 1)
            if status != 52:
                raise Exception("failed to set PID value for instruction {}".format(instruction))

        await set_val(0x01, p)
        await set_val(0x02, i)
        await set_val(0x03, d)
        await set_val(0x04, error_accum_max)

        if save:
            await self.save_pid()

    @i2c_retry(N_I2C_TRIES)
    async def set_point(self, point):
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x07] + list(struct.pack("1f", point)), 1)
        if status != 52:
            raise Exception("failed to set the PID \"set point\"")

    @i2c_retry(N_I2C_TRIES)
    async def enable(self, invert_output=False):
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x08, (0x01 if invert_output else 0x00)], 1)
        if status != 52:
            raise Exception("failed to enable PID loop")

    @i2c_retry(N_I2C_TRIES)
    async def disable(self):
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x00], 1)
        if status != 52:
            raise Exception("failed to disable PID loop")

    async def save_pid(self):
        """
        Save P, I, D (and `error_accum_max`) to the EEPROM.
        This is a non-standard method which is not part of the PID interface.
        """
        @i2c_retry(N_I2C_TRIES)
        async def save():
            status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x05], 1)
            if status != 52:
                raise Exception("failed to save PID params")

        @i2c_retry(N_I2C_TRIES)
        async def is_saved():
            status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x06], 1)
            return status == 0

        await save()
        await i2c_poll_until(is_saved, True, timeout_ms=1000)


KNOWN_COMPONENTS = {
    'VersionInfo':           VersionInfo,
    'Credentials':           Credentials,
    'LoopFrequency':         LoopFrequency,
    'BatteryVoltageReader':  BatteryVoltageReader,
    'Buzzer':                Buzzer,
    'Gyroscope':             Gyroscope,
    'Gyroscope_accum':       GyroscopeAccum,
    'Accelerometer':         Accelerometer,
    'PushButtons':           PushButtons,
    'LEDs':                  LEDs,
    'Photoresistor':         Photoresistor,
    'Encoders':              Encoders,
    'CarMotors':             CarMotors,
    'PWMs':                  PWMs,
    'Calibrator':            Calibrator,
    'PID_steering':          PidSteering,
}

