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
                      write_read_i2c,
                      i2c_retry, i2c_poll_until)

from . import N_I2C_TRIES

from .db import default_db
from .battery_discharge_curve import battery_map_millivolts_to_percentage

from . import imu

from .camera_async import CameraRGB_Async
from .camera_pi import CameraRGB

import cio

from auto import logger
log = logger.init(__name__, terminal=True)

import os
import time
import struct
import asyncio
import subprocess
from math import floor, isnan
from collections import deque


import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)   # GPIO.BOARD or GPIO.BCM

POWER_BUTTON_PIN = 29
GPIO.setup(POWER_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

PUSH_BUTTON_PINS = [32, 33, 36]
for pin in PUSH_BUTTON_PINS:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)


class VersionInfo(cio.VersionInfoIface):
    def __init__(self, fd, reg_num):
        self.fd = fd
        self.reg_num = reg_num

    async def acquired(self):
        pass

    async def released(self):
        pass

    async def name(self):
        return "AutoAuto v3 Controller"

    @i2c_retry(N_I2C_TRIES)
    async def version(self):
        major, minor = await write_read_i2c_with_integrity(self.fd, [self.reg_num], 2)
        return major, minor


class Credentials(cio.CredentialsIface):
    def __init__(self, fd, reg_num):
        self.fd = fd
        self.db = None
        self.loop = asyncio.get_running_loop()

    async def acquired(self):
        pass

    async def released(self):
        pass

    async def get_labs_auth_code(self):
        db_record = await self.loop.run_in_executor(None, self._db_get_labs_auth_code)
        if db_record is not None:
            log.info('Querying labs auth code; found in database.')
            return db_record
        eeprom_record = await self._eeprom_get_labs_auth_code()
        if eeprom_record is not None:
            # It's in the EEPROM, but not the DB. So, copy it over to the DB so we find it there next time.
            log.info('Querying labs auth code; found in eeprom; copying to database.')
            await self.loop.run_in_executor(None, self._db_set_labs_auth_code, eeprom_record)
            return eeprom_record
        log.info('Querying labs auth code; not found.')
        return None

    async def set_labs_auth_code(self, auth_code):
        if (await self.get_labs_auth_code()) is None:
            log.info('Storing labs auth code...')
            await self.loop.run_in_executor(None, self._db_set_labs_auth_code, auth_code)
            await self._eeprom_set_labs_auth_code(auth_code)
            return True
        else:
            log.info('Will NOT storing labs auth code; it already exits.')
            return False

    async def get_jupyter_password(self):
        db_record = await self.loop.run_in_executor(None, self._db_get_jupyter_password)
        if db_record is not None:
            log.info('Querying Jupyter password; found in database.')
            return db_record
        eeprom_record = await self._eeprom_get_jupyter_password()
        if eeprom_record is not None:
            # It's in the EEPROM, but not the DB. So, copy it over to the DB so we find it there next time.
            log.info('Querying Jupyter password; found in eeprom; copying to database.')
            await self.loop.run_in_executor(None, self._db_set_jupyter_password, eeprom_record)
            return eeprom_record
        log.info('Querying Jupyter password; not found.')
        return None

    async def set_jupyter_password(self, password):
        if (await self.get_jupyter_password()) is None:
            log.info('Storing Jupyter password...')
            await self.loop.run_in_executor(None, self._db_set_jupyter_password, password)
            await self._eeprom_set_jupyter_password(password)
            return True
        else:
            log.info('Will NOT storing Jupyter password; it already exits.')
            return False

    def _get_db(self):
        if self.db is None:
            self.db = default_db()
        return self.db

    def _db_get_labs_auth_code(self):
        return self._get_db().get('DEVICE_LABS_AUTH_CODE', None)

    def _db_set_labs_auth_code(self, auth_code):
        self._get_db().put('DEVICE_LABS_AUTH_CODE', auth_code)
        os.sync()

    def _db_get_jupyter_password(self):
        return self._get_db().get('DEVICE_JUPYTER_PASSWORD', None)

    def _db_set_jupyter_password(self, password):
        self._get_db().put('DEVICE_JUPYTER_PASSWORD', password)
        os.sync()

    async def _eeprom_read_string(self, addr):
        length = (await capabilities.eeprom_query(self.fd, addr, 1))[0]
        if length == 0xFF:
            # Empty record!
            return None
        buf = await capabilities.eeprom_query(self.fd, addr + 1, length)
        return buf.decode()

    async def _eeprom_write_string(self, addr, s):
        buf = bytes([len(s)]) + s.encode()
        await capabilities.eeprom_store(self.fd, addr, buf)

    async def _eeprom_get_labs_auth_code(self):
        return await self._eeprom_read_string(0x00)

    async def _eeprom_set_labs_auth_code(self, auth_code):
        await self._eeprom_write_string(0x00, auth_code)

    async def _eeprom_get_jupyter_password(self):
        return await self._eeprom_read_string(0x30)

    async def _eeprom_set_jupyter_password(self, password):
        await self._eeprom_write_string(0x30, password)


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

    async def acquired(self):
        pass

    async def released(self):
        pass

    async def capture(self):
        return await Camera._camera.capture()


class Power(cio.PowerIface):
    @i2c_retry(N_I2C_TRIES)
    async def _write_reg(self, reg, v):
        buf = bytes([reg, v])
        await write_read_i2c(self.fd, buf, 0)

    @i2c_retry(N_I2C_TRIES)
    async def _read_reg(self, reg):
        buf = bytes([reg])
        readlen = 1
        r = await write_read_i2c(self.fd, buf, readlen)
        v = r[0]
        return v

    @staticmethod
    def _batt_convert_millivolts(v):
        millivolts = 2304
        bit_vals = [20, 40, 80, 160, 320, 640, 1280]
        for i in range(7):
            if v & (1 << i):
                millivolts += bit_vals[i]
        return millivolts

    @staticmethod
    def _input_convert_millivolts(v):
        millivolts = 2600
        bit_vals = [100, 200, 400, 800, 1600, 3200, 6400]
        for i in range(7):
            if v & (1 << i):
                millivolts += bit_vals[i]
        return millivolts

    @staticmethod
    def _charge_current_convert(v):
        milliamps = 0
        bit_vals = [50, 100, 200, 400, 800, 1600, 3200]
        for i in range(7):
            if v & (1 << i):
                milliamps += bit_vals[i]
        return milliamps

    @staticmethod
    def _input_limit_convert(v):
        milliamps = 100
        bit_vals = [50, 100, 200, 400, 800, 1600]
        for i in range(6):
            if v & (1 << i):
                milliamps += bit_vals[i]
        return milliamps

    @staticmethod
    def _is_power_button_pressed():
        return GPIO.input(POWER_BUTTON_PIN) == 0  # active low

    def __init__(self, fd, reg_num):
        self.fd = fd

    async def acquired(self):
        pass

    async def released(self):
        pass

    async def state(self):
        usb_plugged_in = (((await self._read_reg(0x11)) & (1 << 7)) != 0)
        if usb_plugged_in:
            milliamps = await self._read_reg(0x12)
            milliamps = self._charge_current_convert(milliamps)
            return 'charging' if milliamps > 0 else 'wall'
        else:
            return 'battery'

    async def millivolts(self):
        v = await self._read_reg(0x0E)
        millivolts = self._batt_convert_millivolts(v)
        return millivolts

    async def estimate_remaining(self, millivolts=None):
        if millivolts is None:
            millivolts = await self.millivolts()
        percentage = battery_map_millivolts_to_percentage(millivolts)
        minutes = 4.0 * 60.0 * (percentage / 100.0)  # Assumes the full battery lasts 4 hours.
        return floor(minutes), floor(percentage)

    async def charging_info(self):
        """This is a non-standard method."""
        milliamps = await self._read_reg(0x12)
        milliamps = self._charge_current_convert(milliamps)
        input_millivolts = await self._read_reg(0x11)
        input_millivolts = self._input_convert_millivolts(input_millivolts)
        input_milliamps_limit = await self._read_reg(0x00)
        input_milliamps_limit = self._input_limit_convert(input_milliamps_limit)
        return {
            'milliamps': milliamps,
            'input': {
                'millivolts': input_millivolts,
                'milliamps_limit': input_milliamps_limit,
            }
        }

    async def should_shut_down(self):
        curr_state = self._is_power_button_pressed()
        return curr_state

    async def shut_down(self):
        v = await self._read_reg(0x09)
        v |= (1 << 3)
        v |= (1 << 5)
        await self._write_reg(0x09, v)   # <-- tell charger chip to shutdown after a 10-15 second delay
        subprocess.run(['/sbin/poweroff'])

    async def reboot(self):
        subprocess.run(['/sbin/reboot'])


class Buzzer(cio.BuzzerIface):
    def __init__(self, fd, reg_num):
        self.fd = fd
        self.reg_num = reg_num

    async def acquired(self):
        pass

    async def released(self):
        pass

    async def is_currently_playing(self):
        pass   # TODO

    async def wait(self):
        pass   # TODO

    async def play(self, notes="o4l16ceg>c8"):
        pass   # TODO


class Gyroscope(cio.GyroscopeIface):
    def __init__(self, fd, reg_num):
        self.loop = asyncio.get_running_loop()

    async def acquired(self):
        pass

    async def released(self):
        pass

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

    async def acquired(self):
        pass

    async def released(self):
        pass

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

    async def acquired(self):
        pass

    async def released(self):
        pass

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

    async def acquired(self):
        pass

    async def released(self):
        pass

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
    _pin_map = None
    _states = None

    @staticmethod
    def _button_edge_callback(pin):
        button_index = PushButtons._pin_map[pin]
        presses, releases, is_pressed, prev_time = PushButtons._states[button_index]
        curr_time = time.time()
        if curr_time - prev_time < 0.05:
            # Debounced!
            return
        curr_is_pressed = (GPIO.input(pin) == GPIO.LOW)
        if is_pressed == curr_is_pressed:
            # Ignore this... why are we being called when the state has not changed?
            return
        if curr_is_pressed:
            presses += 1
        else:
            releases += 1
        PushButtons._states[button_index] = presses, releases, curr_is_pressed, curr_time

    def __init__(self, fd, reg_num):
        self.n = None
        self.states = None
        self.event_queue = deque()

    async def acquired(self):
        if PushButtons._pin_map is None:
            PushButtons._pin_map = {pin: i for i, pin in enumerate(PUSH_BUTTON_PINS)}
            PushButtons._states = [[0, 0, False, 0] for _ in range(len(PUSH_BUTTON_PINS))]
            for pin in PUSH_BUTTON_PINS:
                GPIO.add_event_detect(pin, GPIO.BOTH, callback=self._button_edge_callback)

    async def released(self):
        pass

    async def num_buttons(self):
        return len(PUSH_BUTTON_PINS)

    async def button_state(self, button_index):
        presses, releases, is_pressed, last_event_time = PushButtons._states[button_index]
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

            diff_presses  = state[0] - prev_state[0]
            diff_releases = state[1] - prev_state[1]

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

    async def acquired(self):
        pass

    async def released(self):
        pass

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

    async def acquired(self):
        pass

    async def released(self):
        pass

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

    async def acquired(self):
        pass

    async def released(self):
        pass

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
    params_cache = {}

    @staticmethod
    async def _steering_params(fd, store=None):
        addr = 0xC0
        if store:
            await capabilities.eeprom_store(fd, addr, struct.pack('3B', *store))
        else:
            vals = struct.unpack('3B', await capabilities.eeprom_query(fd, addr, 3))
            if vals == (255, 255, 255):
                vals = (35, 45, 55)
            return vals

    @staticmethod
    async def _safe_speeds(fd, store=None):
        addr = 0xC3
        if store:
            await capabilities.eeprom_store(fd, addr, struct.pack('2b', *store))
        else:
            vals = struct.unpack('2b', await capabilities.eeprom_query(fd, addr, 2))
            if vals == (-1, -1):
                vals = (-40, 40)
            return vals

    @classmethod
    async def _cached_stuff(cls, fd, name, func):
        vals = cls.params_cache.get(name)
        if vals is None:
            vals = await func(fd)
            cls.params_cache[name] = vals
        return vals

    @classmethod
    async def _store_stuff(cls, fd, name, func, vals):
        await func(fd, vals)
        cls.params_cache[name] = vals

    async def get_steering_params(self):
        return await self._cached_stuff(self.fd, 'steering_params', self._steering_params)

    async def set_steering_params(self, vals):
        return await self._store_stuff(self.fd, 'steering_params', self._steering_params, vals)

    async def get_safe_speeds(self):
        return await self._cached_stuff(self.fd, 'safe_speeds', self._safe_speeds)

    async def set_safe_speeds(self, vals):
        return await self._store_stuff(self.fd, 'safe_speeds', self._safe_speeds, vals)

    @staticmethod
    def interp(a, b, c, x, y, z, val):
        val = min(max(val, x), z)
        if val < y:
            return (val - x) / (y - x) * (b - a) + a
        else:
            return (val - y) / (z - y) * (c - b) + b

    def __init__(self, fd, reg_num):
        self.fd = fd
        self.reg_num = reg_num

    async def acquired(self):
        pass

    async def released(self):
        await self.off()

    @i2c_retry(N_I2C_TRIES)
    async def on(self):
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x00], 1)
        if status != 105:
            raise Exception("failed to turn on car motors")

    @i2c_retry(N_I2C_TRIES)
    async def set_steering(self, steering):
        low, mid, high = await self.get_steering_params()
        val = self.interp(low, mid, high, -45, 0, 45, steering)
        val = int(round(val))
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x01, val], 1)
        if status != 105:
            raise Exception("failed to set steering")

    @i2c_retry(N_I2C_TRIES)
    async def set_throttle(self, throttle):
        val = self.interp(10000, 0, 10000, -100, 0, 100, throttle)
        val = int(round(val))
        d = 0 if throttle >= 0 else 1
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x02, *struct.pack('H', val), d], 1)
        if status != 105:
            raise Exception("failed to set throttle")

    async def get_safe_throttle(self):
        return await self.get_safe_speeds()

    async def set_safe_throttle(self, min_throttle, max_throttle):
        return await self.set_safe_speeds((min_throttle, max_throttle))

    @i2c_retry(N_I2C_TRIES)
    async def off(self):
        status, = await write_read_i2c_with_integrity(self.fd, [self.reg_num, 0x03], 1)
        if status != 105:
            raise Exception("failed to turn off car motors")

    def rpc_extra_exports(self):
        return ['get_steering_params', 'set_steering_params']


class Calibrator(cio.CalibratorIface):  # TODO
    def __init__(self, fd, reg_num):
        pass

    async def acquired(self):
        pass

    async def released(self):
        pass

    async def start(self):
        pass  # no-op

    async def status(self):
        pass  # no-op

    async def script_name(self):
        return "calibrate_car_v3"


class PidSteering(cio.PidSteeringIface):  # TODO
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

    async def acquired(self):
        pass

    async def released(self):
        pass

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
    'Camera':                Camera,
    'Power':                 Power,
    'Buzzer':                Buzzer,
    'Gyroscope':             Gyroscope,
    'Gyroscope_accum':       GyroscopeAccum,
    'Accelerometer':         Accelerometer,
    'AHRS':                  Ahrs,
    'PushButtons':           PushButtons,
    'LEDs':                  LEDs,
    'ADC':                   ADC,
    'Photoresistor':         Photoresistor,
    'CarMotors':             CarMotors,
    'Calibrator':            Calibrator,
    'PID_steering':          PidSteering,
}


from . import capabilities

