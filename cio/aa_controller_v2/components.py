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

from . import imu

from .camera_async import CameraRGB_Async
from .camera_pi import CameraRGB

import cio

import os
import time
import struct
import asyncio
import subprocess
from math import floor, isnan
from collections import deque

import numpy as np


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
        os.sync()

    def _get_jupyter_password(self):
        return self._get_db().get('DEVICE_JUPYTER_PASSWORD', None)

    def _set_jupyter_password(self, password):
        self._get_db().put('DEVICE_JUPYTER_PASSWORD', password)
        os.sync()


class Camera(cio.CameraIface):
    _camera = None

    def __init__(self, fd, reg_num):
        if Camera._camera is None:
            loop = asyncio.get_running_loop()
            Camera._camera = CameraRGB_Async(
                    lambda: CameraRGB(width=320, height=240, fps=8),
                    loop=loop,
                    idle_timeout=30
            )

    async def capture(self):
        return await Camera._camera.capture()


class LoopFrequency(cio.LoopFrequencyIface):
    def __init__(self, fd, reg_num):
        self.fd = fd
        self.reg_num = reg_num

    @i2c_retry(N_I2C_TRIES)
    async def read(self):
        buf = await write_read_i2c_with_integrity(self.fd, [self.reg_num], 4)
        return struct.unpack('1I', buf)[0]


class Power(cio.PowerIface):
    def __init__(self, fd, reg_num):
        self.fd = fd
        self.reg_num = reg_num

    async def state(self):
        return 'battery'

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

    @i2c_retry(N_I2C_TRIES)
    async def should_shut_down(self):
        on_flag, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x01], 1)
        return not on_flag

    async def shut_down(self):
        subprocess.run(['/sbin/poweroff'])

    async def reboot(self):
        subprocess.run(['/sbin/reboot'])


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
        self.loop = asyncio.get_running_loop()

    def _read(self):
        with imu.COND:
            imu.COND.wait()
            t = imu.DATA['timestamp']
            x, y, z = imu.DATA['gyro']
        return t, x, y, z

    async def read(self):
        vals = await self.loop.run_in_executor(None, self._read)
        return vals[1:]

    async def read_t(self):
        """This is a non-standard method."""
        vals = await self.loop.run_in_executor(None, self._read)
        return vals


class GyroscopeAccum(cio.GyroscopeAccumIface):
    def __init__(self, fd, reg_num):
        self.loop = asyncio.get_running_loop()
        self.offsets = None

    def _reset(self):
        self.offsets = self._read_raw()[1:]

    def _read_raw(self):
        with imu.COND:
            imu.COND.wait()
            t = imu.DATA['timestamp']
            x, y, z = imu.DATA['gyro_accum']
        return t, x, y, z

    async def reset(self):
        await self.loop.run_in_executor(None, self._reset)

    async def read(self):
        t, x, y, z = await self.read_t()
        return x, y, z

    async def read_t(self):
        """This is a non-standard method."""
        t, x, y, z = await self.loop.run_in_executor(None, self._read_raw)
        vals = x, y, z
        if self.offsets is None:
            self.offsets = vals
        new_vals = tuple([(val - offset) for val, offset in zip(vals, self.offsets)])
        return (t,) + new_vals


class Accelerometer(cio.AccelerometerIface):
    def __init__(self, fd, reg_num):
        self.loop = asyncio.get_running_loop()

    def _read(self):
        with imu.COND:
            imu.COND.wait()
            t = imu.DATA['timestamp']
            x, y, z = imu.DATA['accel']
        return t, x, y, z

    async def read(self):
        vals = await self.loop.run_in_executor(None, self._read)
        return vals[1:]

    async def read_t(self):
        """This is a non-standard method."""
        vals = await self.loop.run_in_executor(None, self._read)
        return vals


class Ahrs(cio.AhrsIface):
    def __init__(self, fd, reg_num):
        self.loop = asyncio.get_running_loop()

    def _read(self):
        with imu.COND:
            imu.COND.wait()
            t = imu.DATA['timestamp']
            roll, pitch, yaw = imu.DATA['ahrs']
        return t, roll, pitch, yaw

    async def read(self):
        vals = await self.loop.run_in_executor(None, self._read)
        return vals[1:]

    async def read_t(self):
        """This is a non-standard method."""
        vals = await self.loop.run_in_executor(None, self._read)
        return vals


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

    async def set_brightness(self, brightness):
        raise Exception('LED brightness not available on this hardware.')


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
        self.last_counts = {}
        self.abs_counts  = {}

    async def num_encoders(self):
        return 2

    async def enable(self, encoder_index):
        if encoder_index == 0:
            return await self._enable_e1()
        else:
            return await self._enable_e2()

    async def read_counts(self, encoder_index):
        if encoder_index == 0:
            vals = await self._read_e1_counts()
        else:
            vals = await self._read_e2_counts()
        vals = list(vals)
        vals[0] = self._fix_count_rollover(vals[0], encoder_index)
        vals = tuple(vals)
        return vals

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

    def _fix_count_rollover(self, count, encoder_index):
        count = np.int16(count)
        if encoder_index not in self.last_counts:
            self.last_counts[encoder_index] = count
            self.abs_counts[encoder_index] = 0
            return 0
        diff = int(count - self.last_counts[encoder_index])
        self.last_counts[encoder_index] = count
        abs_count = self.abs_counts[encoder_index] + diff
        self.abs_counts[encoder_index] = abs_count
        return abs_count


class CarMotors(cio.CarMotorsIface):
    safe_throttle_cache = None

    def __init__(self, fd, reg_num):
        self.fd = fd
        self.reg_num = reg_num

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

    @i2c_retry(N_I2C_TRIES)
    async def _get_safe_throttle(self):
        buf = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x09], 4)
        min_throttle, max_throttle = struct.unpack('2h', buf)
        return min_throttle, max_throttle

    @i2c_retry(N_I2C_TRIES)
    async def _set_safe_throttle(self, min_throttle, max_throttle):
        payload = list(struct.pack('2h', min_throttle, max_throttle))
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x0A] + payload, 1)
        if status != 104:
            raise Exception('failed to set params: min_throttle and max_throttle')
        await self.save_params()

    async def get_safe_throttle(self):
        if CarMotors.safe_throttle_cache is None:
            CarMotors.safe_throttle_cache = await self._get_safe_throttle()
        return CarMotors.safe_throttle_cache

    async def set_safe_throttle(self, min_throttle, max_throttle):
        CarMotors.safe_throttle_cache = (min_throttle, max_throttle)
        return await self._set_safe_throttle(min_throttle, max_throttle)

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
        pass

    async def start(self):
        pass  # no-op

    async def status(self):
        pass  # no-op

    async def script_name(self):
        return "calibrate_car_v2"


class PidSteering(cio.PidSteeringIface):
    pid_cache = None

    def __init__(self, fd, reg_nums):
        self.fd = fd
        self.p = None
        self.i = None
        self.d = None
        self.error_accum_max = None
        self.point = 0.0
        carmotors_regnum, gyroaccum_regnum = reg_nums
        self.carmotors = CarMotors(fd, carmotors_regnum)
        self.gyroaccum = GyroscopeAccum(fd, gyroaccum_regnum)
        self.task = None

    async def set_pid(self, p, i, d, error_accum_max=0.0, save=False):
        self.p = p
        self.i = i
        self.d = d
        self.error_accum_max = error_accum_max

        if save:
            await capabilities.eeprom_store(self.fd, 0xB0, struct.pack('1f', self.p))
            await capabilities.eeprom_store(self.fd, 0xB4, struct.pack('1f', self.i))
            await capabilities.eeprom_store(self.fd, 0xB8, struct.pack('1f', self.d))
            await capabilities.eeprom_store(self.fd, 0xBC, struct.pack('1f', self.error_accum_max))
            PidSteering.pid_cache = (self.p, self.i, self.d, self.error_accum_max)

    async def set_point(self, point):
        self.point = point

    async def enable(self, invert_output=False):
        if self.p is None:
            if PidSteering.pid_cache is not None:
                 self.p, self.i, self.d, self.error_accum_max = PidSteering.pid_cache
            else:
                self.p,               = struct.unpack('1f', await capabilities.eeprom_query(self.fd, 0xB0, 4))
                self.i,               = struct.unpack('1f', await capabilities.eeprom_query(self.fd, 0xB4, 4))
                self.d,               = struct.unpack('1f', await capabilities.eeprom_query(self.fd, 0xB8, 4))
                self.error_accum_max, = struct.unpack('1f', await capabilities.eeprom_query(self.fd, 0xBC, 4))
                PidSteering.pid_cache = (self.p, self.i, self.d, self.error_accum_max)

        if isnan(self.p):
            self.p = 1.0
        if isnan(self.i):
            self.i = 0.0
        if isnan(self.d):
            self.d = 0.0
        if isnan(self.error_accum_max):
            self.error_accum_max = 0.0

        await self.disable()
        self.task = asyncio.create_task(self._task_main(invert_output))

    async def disable(self):
        if self.task is not None:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass # this is expected
            self.task = None

    async def _task_main(self, invert_output):
        last_t = None
        error_accum = 0.0
        last_error = None

        while True:
            t, _, _, z = await self.gyroaccum.read_t()

            dt = ((t - last_t) if last_t is not None else 0.0) * 0.000001
            last_t = t

            curr_error = self.point - z

            p_part = self.p * curr_error

            error_accum += curr_error * dt
            if self.error_accum_max > 0.0:
                if error_accum > self.error_accum_max:
                    error_accum = self.error_accum_max
                elif error_accum < -self.error_accum_max:
                    error_accum = -self.error_accum_max

            i_part = self.i * error_accum

            error_diff = ((curr_error - last_error) / dt) if last_error is not None else 0.0
            last_error = curr_error

            d_part = self.d * error_diff

            output = p_part + i_part + d_part
            if invert_output:
                output = -output

            await self.carmotors.set_steering(output)


class CarControl(cio.CarControlIface):
    def __init__(self, fd, reg_nums):
        self.car_motors = CarMotors(fd, reg_nums[0])
        self.gyro_accum = GyroscopeAccum(fd, reg_nums[1]) if len(reg_nums) > 1 else None
        self.pid_steering = PidSteering(fd, (reg_nums[0], reg_nums[1])) if len(reg_nums) > 1 else None

    async def on(self):
        await self.car_motors.on()

    async def straight(self, throttle, sec=None, cm=None):
        if cm is not None:
            raise ValueError('This device does not have a wheel encoder, thus you may not pass `cm` to travel a specific distance.')

        if sec is None:
            raise ValueError('You must specify `sec`, the number of seconds to drive.')

        await self.car_motors.set_steering(0.0)
        await asyncio.sleep(0.1)

        if self.pid_steering is not None and self.gyro_accum is not None:
            _, _, z = await self.gyro_accum.read()
            start_time = time.time()
            await self.pid_steering.set_point(z)
            await self.pid_steering.enable(invert_output=(throttle < 0))
        else:
            start_time = time.time()

        while True:
            curr_time = time.time()
            if curr_time - start_time >= sec:
                break
            await self.car_motors.set_throttle(throttle)
            if self.pid_steering is None:
                await self.car_motors.set_steering(0.0)
            await asyncio.sleep(min(0.1, curr_time - start_time))

        await self.car_motors.set_throttle(0.0)
        await asyncio.sleep(0.1)
        if self.pid_steering is not None:
            await self.pid_steering.disable()

    async def drive(self, steering, throttle, sec=None, deg=None):
        if sec is not None and deg is not None:
            raise Exception('You may not specify both `sec` and `deg`.')

        if sec is None and deg is None:
            raise Exception('You must specify either `sec` or `deg`.')

        if deg is not None and self.gyro_accum is None:
            raise Exception('This device has no gyroscope, so you may not pass `deg`.')

        if deg is not None and deg <= 0.0:
            raise Exception('You must pass `deg` as a postive value.')

        await self.car_motors.set_steering(steering)
        await asyncio.sleep(0.1)
        start_time = time.time()

        if sec is not None:
            while True:
                curr_time = time.time()
                if curr_time - start_time >= sec:
                    break
                await self.car_motors.set_throttle(throttle)
                await self.car_motors.set_steering(steering)
                await asyncio.sleep(min(0.1, curr_time - start_time))

        elif deg is not None:
            await self.gyro_accum.reset()  # Start the gyroscope reading at 0.
            throttle_time = time.time()
            await self.car_motors.set_throttle(throttle)
            while True:
                x, y, z = await self.gyro_accum.read()
                if abs(z) >= deg:
                    break
                curr_time = time.time()
                if curr_time - throttle_time > 0.75:
                    await self.car_motors.set_throttle(throttle)
                    await self.car_motors.set_steering(steering)
                    throttle_time = curr_time

        await self.car_motors.set_throttle(0.0)
        await asyncio.sleep(0.1)

    async def off(self):
        await self.car_motors.off()


KNOWN_COMPONENTS = {
    'VersionInfo':           VersionInfo,
    'Credentials':           Credentials,
    'Camera':                Camera,
    'LoopFrequency':         LoopFrequency,
    'Power':                 Power,
    'Buzzer':                Buzzer,
    'Gyroscope':             Gyroscope,
    'Gyroscope_accum':       GyroscopeAccum,
    'Accelerometer':         Accelerometer,
    'AHRS':                  Ahrs,
    'PushButtons':           PushButtons,
    'LEDs':                  LEDs,
    'Photoresistor':         Photoresistor,
    'Encoders':              Encoders,
    'CarMotors':             CarMotors,
    'PWMs':                  PWMs,
    'Calibrator':            Calibrator,
    'PID_steering':          PidSteering,
    'CarControl':            CarControl,
}


from . import capabilities

