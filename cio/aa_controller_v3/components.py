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

import cio

import os
import struct
import asyncio
from math import floor, isnan
from collections import deque

import numpy as np


class VersionInfo(cio.VersionInfoIface):
    def __init__(self, fd, reg_num):
        self.fd = fd
        self.reg_num = reg_num

    async def name(self):
        return "AutoAuto v3 Controller"

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


class BatteryVoltageReader(cio.BatteryVoltageReaderIface):   # TODO
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

    @i2c_retry(N_I2C_TRIES)
    async def should_shut_down(self):
        on_flag, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x01], 1)
        return not on_flag


class Buzzer(cio.BuzzerIface):   # TODO
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


class Gyroscope(cio.GyroscopeIface):  # TODO
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


class GyroscopeAccum(cio.GyroscopeAccumIface):  # TODO
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


class Accelerometer(cio.AccelerometerIface):  # TODO
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


class Ahrs(cio.AhrsIface):  # TODO
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


class PushButtons(cio.PushButtonsIface):  # TODO
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
        self.NUM_LEDS = 6
        self.vals = [None for index in range(self.NUM_LEDS)]  # using `None`, so that fist call to _set() actually sets it, no matter what the value

    async def led_map(self):
        return {index: 'RGB LED at index {}'.format(index) for index in range(self.NUM_LEDS)}

    @i2c_retry(N_I2C_TRIES)
    async def _set(self, index, val):
        if not isinstance(index, int):
            raise ValueError('You must pass an integer for the led identifier parameter.')
        if index < 0 or index >= self.NUM_LEDS:
            raise ValueError('The index {} is out of range.'.format(index))
        if isinstance(val, int):
            r, g, b = val, val, val
        elif isinstance(val, (tuple, list)):
            r, g, b = val
        else:
            raise ValueError('You must pass the LED value as a three-tuple denoting the three RGB values.')
        if self.vals[index] == val:
            return
        self.vals[index] = val
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x00, index, r, g, b], 1)
        if status != 72:
            raise Exception("failed to set LED state")

    @i2c_retry(N_I2C_TRIES)
    async def _show(self):
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x02], 1)
        if status != 72:
            raise Exception("failed to set LED state")

    async def set_led(self, led_identifier, val):
        await self._set(led_identifier, val)
        await self._show()

    async def set_many_leds(self, id_val_list):
        for led_identifier, val in id_val_list:
            await self._set(led_identifier, val)
        await self._show()

    async def mode_map(self):
        return {
            'spin': 'Spin colors around the six primary LEDs.',
            'pulse': 'Pulse on all LEDs the value of the LED at index 0.',
        }

    @i2c_retry(N_I2C_TRIES)
    async def set_mode(self, mode_identifier):
        mode = 0
        if mode_identifier == 'spin':
            mode = 1
        elif mode_identifier == 'pulse':
            mode = 2
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x03, mode], 1)
        if status != 72:
            raise Exception("failed to set LED mode")

    @i2c_retry(N_I2C_TRIES)
    async def _set_brightness(self, brightness):
        if brightness > 50:
            brightness = 50
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x01, brightness], 1)
        if status != 72:
            raise Exception("failed to set LED mode")

    async def set_brightness(self, brightness):
        await self._set_brightness(brightness)
        await self._show()


class ADC(cio.AdcIface):
    def __init__(self, fd, reg_num):
        self.fd = fd
        self.reg_num = reg_num

    async def num_pins(self):
        return 1

    @i2c_retry(N_I2C_TRIES)
    async def read(self, index):
        if index != 0:
            raise ValueError(f'Invalid index: {index}')
        buf = await write_read_i2c_with_integrity(self.fd, [self.reg_num], 2)
        volts, = struct.unpack('H', buf)
        return volts / 1023 * 3.3


class Photoresistor(cio.PhotoresistorIface):
    def __init__(self, fd, reg_num):
        self.adc = ADC(fd, reg_num)

    async def read(self):
        volts = await self.adc.read(0)
        if volts == 0:
            return volts, float("inf")
        KNOWN_RESISTANCE = 470000
        resistance = (3.3 - volts) * KNOWN_RESISTANCE / volts
        millivolts = volts * 1000
        return millivolts, resistance

    async def read_millivolts(self):
        millivolts, resistance = await self.read()
        return millivolts

    async def read_ohms(self):
        millivolts, resistance = await self.read()
        return resistance


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
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x01, steering & 0xFF], 1)
        if status != 104:
            raise Exception("failed to set steering")

    @i2c_retry(N_I2C_TRIES)
    async def set_throttle(self, throttle):
        throttle = int(round(min(max(throttle, -100), 100)))
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x02, throttle & 0xFF], 1)
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

    async def set_params(self, steering_left, steering_mid, steering_right, steering_millis,
                         throttle_forward, throttle_mid, throttle_reverse, throttle_millis):
        """
        Set the car motors' PWM signal parameters.
        This is a non-standard method which is not a part of the CarMotors interface.
        """
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
        return "calibrate_car_v3"


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


KNOWN_COMPONENTS = {
    'VersionInfo':           VersionInfo,
    'Credentials':           Credentials,
    'BatteryVoltageReader':  BatteryVoltageReader,
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
}


from . import capabilities

