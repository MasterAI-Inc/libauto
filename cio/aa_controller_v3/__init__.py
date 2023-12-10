###############################################################################
#
# Copyright (c) 2017-2023 Master AI, Inc.
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from Master AI, Inc.
#
###############################################################################

"""
This package contains the interface to AutoAuto v3 microcontroller which we
communicate with via UART.
"""

import asyncio
import os
import subprocess
import math
import time
import struct

from collections import deque

from auto.buzzer_lang import BuzzParser

import cio

from .proto import Proto
from .db import default_db
from .battery_discharge_curve import battery_map_millivolts_to_percentage
from .camera_async import CameraRGB_Async
from .camera_pi import CameraRGB
from . import imu_util

from auto import logger
log = logger.init(__name__, terminal=True)


class CioRoot(cio.CioRoot):
    """
    This is the CIO root interface for the AutoAuto v3.x microcontrollers.
    """
    def __init__(self):
        self.proto = None
        self.impls = {
            'VersionInfo': VersionInfo,
            'Credentials': Credentials,
            'Camera': Camera,
            'LoopFrequency': LoopFrequency,
            'Power': Power,
            'Buzzer': Buzzer,
            'Gyroscope': Gyroscope,
            'Gyroscope_accum': GyroscopeAccum,
            'Accelerometer': Accelerometer,
            'AHRS': Ahrs,
            'PushButtons': PushButtons,
            'LEDs': LEDs,
            'Photoresistor': Photoresistor,
            'Encoders': Encoders,
            'CarMotors': CarMotors,
            'Calibrator': Calibrator,
            'CarControl': CarControl,
        }
        self.refcounts = {}   # maps `capability_id` to integer refcount
        self.objects = {}     # maps `capability_id` to first object of that type
        self.lock = asyncio.Lock()

    async def init(self):
        async with self.lock:
            if self.proto is not None:
                return list(self.impls.keys())

            self.proto = Proto(log)

            try:
                major, minor = await self.proto.version(timeout=2.0)
                if major != 3:
                    raise Exception('Controller is not version 3, thus this interface will not work.')
            except:
                self.proto.close()
                self.proto = None
                raise

            await self.proto.init()

            return list(self.impls.keys())

    async def acquire(self, capability_id):
        async with self.lock:
            if capability_id not in self.impls:
                raise Exception(f"Unknown capability: {capability_id}")
            capability_obj = self.impls[capability_id](self.proto)
            capability_obj._cio_root = self
            capability_obj._capability_id = capability_id
            if capability_id not in self.refcounts:
                self.refcounts[capability_id] = 1
                self.objects[capability_id] = capability_obj
                await capability_obj.acquired(first=True)
            else:
                refcount = self.refcounts[capability_id]
                self.refcounts[capability_id] = refcount + 1
                await capability_obj.acquired(first=False)
            return capability_obj

    async def release(self, capability_obj):
        async with self.lock:
            capability_id = capability_obj._capability_id
            if capability_id not in self.refcounts:
                raise Exception("Invalid object passed to `release()`")
            refcount = self.refcounts[capability_id]
            refcount -= 1
            if refcount == 0:
                del self.refcounts[capability_id]
                del self.objects[capability_id]
                await capability_obj.released(last=True)
            else:
                self.refcounts[capability_id] = refcount
                await capability_obj.released(last=False)

    async def close(self):
        async with self.lock:
            for capability_obj in self.objects.values():
                await capability_obj.released(last=True)
            self.refcounts = {}
            self.objects = {}
            if self.proto is not None:
                self.proto.close()
                self.proto = None


class VersionInfo(cio.VersionInfoIface):
    def __init__(self, proto):
        self.proto = proto

    async def acquired(self, first):
        pass

    async def name(self):
        return "AutoAuto v3 Controller"

    async def version(self):
        return await self.proto.version()

    async def released(self, last):
        pass


class Credentials(cio.CredentialsIface):
    def __init__(self, _proto):
        self.db = None
        self.loop = asyncio.get_running_loop()
        # TODO: back up to EEPROM?

    async def acquired(self, first):
        pass

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

    async def released(self, last):
        pass

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

    def __init__(self, _proto):
        if Camera._camera is None:
            loop = asyncio.get_running_loop()
            Camera._camera = CameraRGB_Async(
                    lambda: CameraRGB(width=320, height=240, fps=8),
                    loop=loop,
                    idle_timeout=30
            )

    async def acquired(self, first):
        pass

    async def capture(self):
        return await Camera._camera.capture()

    async def released(self, last):
        pass


class LoopFrequency(cio.LoopFrequencyIface):
    def __init__(self, proto):
        self.proto = proto

    async def acquired(self, first):
        pass

    async def read(self):
        return self.proto.loop_freq

    async def released(self, last):
        pass


class Power(cio.PowerIface):
    def __init__(self, proto):
        self.proto = proto

    async def acquired(self, first):
        pass

    async def state(self):
        return 'charging' if self.proto.is_charging() else 'battery'

    async def millivolts(self):
        vbatt1, vbatt2, vchrg = self.proto.voltages
        return vbatt2

    async def estimate_remaining(self, millivolts=None):
        if millivolts is None:
            millivolts = await self.millivolts()
        percentage = battery_map_millivolts_to_percentage(millivolts)
        minutes = 6.0 * 60.0 * (percentage / 100.0)  # Assumes the full battery lasts 6 hours (based on our lab tests)
        return math.floor(minutes), math.floor(percentage)

    async def should_shut_down(self):
        return False

    async def shut_down(self):
        subprocess.run(['/sbin/poweroff'])

    async def reboot(self):
        subprocess.run(['/sbin/reboot'])

    async def released(self, last):
        pass


class Buzzer(cio.BuzzerIface):
    _is_playing = False

    def __init__(self, proto):
        self.proto = proto
        self.buzz_parser = BuzzParser()
        self.iamplaying = False
        self.active = False

    async def acquired(self, first):
        self.active = True

    async def is_currently_playing(self):
        return Buzzer._is_playing

    async def wait(self):
        while await self.is_currently_playing():
            # Lame implementation, but good enough for this method's purpose.
            await asyncio.sleep(0.1)

    async def play(self, notes="o4l16ceg>c8"):
        if not notes:
            return

        note_tuples, _total_time = self.buzz_parser.convert(notes)

        await self.wait()

        if Buzzer._is_playing:
            # RACE CONDITION: Someone beat you to it.
            raise Exception('Buzzer is currently playing, so you cannot submit more notes right now.')

        Buzzer._is_playing = True
        self.iamplaying = True
        try:
            for freqHz, durationMS, _volume in note_tuples:
                await self.proto.buzzer_play(freqHz, durationMS)
                if not self.active:
                    break
        finally:
            self.iamplaying = False
            Buzzer._is_playing = False

    async def released(self, last):
        self.active = False
        if self.iamplaying:
            await self.proto.buzzer_stop()


class Gyroscope(cio.GyroscopeIface):
    def __init__(self, proto):
        self.proto = proto

    async def acquired(self, first):
        await self.proto.imu_acquire()

    async def read(self):
        await self.proto.wait_imu_tick()
        return tuple(self.proto.gyrovals)

    async def released(self, last):
        await self.proto.imu_release()


class GyroscopeAccum(cio.GyroscopeAccumIface):
    def __init__(self, proto):
        self.proto = proto
        self.offsets = None

    async def acquired(self, first):
        await self.proto.imu_acquire()

    async def reset(self):
        self.offsets = tuple(self.proto.gyroaccumvals)

    async def read(self):
        await self.proto.wait_imu_tick()
        vals = tuple(self.proto.gyroaccumvals)
        if self.offsets is None:
            self.offsets = vals
        return tuple((val - offset) for val, offset in zip(vals, self.offsets))

    async def released(self, last):
        await self.proto.imu_release()


class Accelerometer(cio.AccelerometerIface):
    def __init__(self, proto):
        self.proto = proto

    async def acquired(self, first):
        await self.proto.imu_acquire()

    async def read(self):
        await self.proto.wait_imu_tick()
        return tuple(self.proto.accelvals)

    async def released(self, last):
        await self.proto.imu_release()


class Ahrs(cio.AhrsIface):
    def __init__(self, proto):
        self.proto = proto

    async def acquired(self, first):
        await self.proto.imu_acquire()

    async def read(self):
        await self.proto.wait_imu_tick()
        q = tuple(self.proto.quaternion)
        return imu_util.roll_pitch_yaw(q)

    async def released(self, last):
        await self.proto.imu_release()


class PushButtons(cio.PushButtonsIface):
    def __init__(self, proto):
        self.proto = proto
        self.events = []
        self.addevents = lambda events: self.events.extend(events)
        self.event_queue = deque()

    async def acquired(self, first):
        self.proto.buttonlisteners.append(self.addevents)

    async def num_buttons(self):
        return len(self.proto.buttonstate)

    async def button_state(self, button_index):
        return self.proto.buttonstate[button_index]

    async def get_events(self):
        events = self.events
        self.events = []
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

    async def released(self, last):
        self.proto.buttonlisteners.remove(self.addevents)


class LEDs(cio.LEDsIface):
    def __init__(self, proto):
        self.proto = proto
        self.NUM_LEDS = 3
        self.vals = [None for index in range(self.NUM_LEDS)]  # using `None`, so that fist call to _set() actually sets it, no matter what the value
        self.brightness = None

    async def acquired(self, first):
        pass

    async def led_map(self):
        return {index: 'RGB LED at index {}'.format(index) for index in range(self.NUM_LEDS)}

    async def set_led(self, led_identifier, val):
        await self._set(led_identifier, val)

    async def set_many_leds(self, id_val_list):
        for led_identifier, val in id_val_list:
            await self._set(led_identifier, val)

    async def mode_map(self):
        return {}

    async def set_mode(self, mode_identifier):
        raise NotImplementedError('no modes are currently supported')

    async def set_brightness(self, brightness):
        if not isinstance(brightness, int) or brightness < 0 or brightness > 255:
            raise ValueError(f'brightness must be an integer in the range [0, 255]')
        if brightness > 0:
            changed = self.brightness != brightness
            self.brightness = brightness
        else:
            changed = self.brightness is not None
            self.brightness = None
        if changed:
            for i, v in enumerate(self.vals):
                if v is not None:
                    await self.proto.set_led(i, v, self.brightness)

    async def _set(self, index, val):
        if not isinstance(index, int):
            raise ValueError('You must pass an integer for the led identifier parameter.')
        if index < 0 or index >= self.NUM_LEDS:
            raise ValueError(f'The index {index} is out of range.')
        if isinstance(val, (int, float)) and 0.0 <= val <= 1.0:
            val = float(val)
            val = val, val, val
        elif isinstance(val, (tuple, list)) and len(val) == 3 and all([isinstance(v, (int, float)) for v in val]) and all([(0.0 <= v <= 1.0) for v in val]):
            val = tuple([float(v) for v in val])
        else:
            raise ValueError('You must pass the LED value as a single value or a three-tuple denoting the three RGB values, where each value is in the range [0.0, 1.0].')
        if self.vals[index] == val:
            return
        self.vals[index] = val
        await self.proto.set_led(index, val, self.brightness)

    async def _reset(self):
        for index in range(self.NUM_LEDS):
            await self._set(index, (0, 0, 0))

    async def released(self, last):
        if last:
            await self._reset()


class Photoresistor(cio.PhotoresistorIface):
    def __init__(self, proto):
        self.proto = proto

    async def acquired(self, first):
        await self.proto.photoresistor_acquire()

    async def read(self):
        await self.proto.photoresistor_tick()
        millivolts, resistance = self.proto.photoresistor_vals
        return millivolts, resistance

    async def read_millivolts(self):
        millivolts, resistance = await self.read()
        return millivolts

    async def read_ohms(self):
        millivolts, resistance = await self.read()
        return resistance

    async def released(self, last):
        await self.proto.photoresistor_release()


class Encoders(cio.EncodersIface):
    def __init__(self, proto):
        self.proto = proto
        self.e1_enabled = False

    async def acquired(self, first):
        pass

    async def num_encoders(self):
        return 1

    async def enable(self, encoder_index):
        if encoder_index != 0:
            raise ValueError('encoder index out of range')
        if not self.e1_enabled:
            self.e1_enabled = True
            await self.proto.encoder_e1_acquire()

    async def read_counts(self, encoder_index):
        if encoder_index != 0:
            raise ValueError('encoder index out of range')
        if not self.e1_enabled:
            raise ValueError('this encoder is not enabled')
        await self.proto.encoder_e1_tick()
        clicks, aCount, bCount, aUpTime, bUpTime = self.proto.encoder_e1_vals
        # TODO: handle overflow? reset to zero on each enable?
        return clicks, aCount, bCount

    async def read_timing(self, encoder_index):
        if encoder_index != 0:
            raise ValueError('encoder index out of range')
        if not self.e1_enabled:
            raise ValueError('this encoder is not enabled')
        await self.proto.encoder_e1_tick()
        clicks, aCount, bCount, aUpTime, bUpTime = self.proto.encoder_e1_vals
        return aUpTime, bUpTime

    async def disable(self, encoder_index):
        if encoder_index != 0:
            raise ValueError('encoder index out of range')
        if self.e1_enabled:
            self.e1_enabled = False
            await self.proto.encoder_e1_release()

    async def released(self, last):
        await self.disable(0)


def lerp(i, f1, f2, t1, t2):
    if i < f1:
        i = f1
    if i > f2:
        i = f2
    return (i - f1) * (t2 - t1) / (f2 - f1) + t1


class CarMotors(cio.CarMotorsIface):
    """
    This class stores calibration settings in the EEPROM at these addresses:

    | addresses       | data                           |
    | --------------- | ------------------------------ |
    | 0x00            | safe throttle reverse          |
    | 0x01            | safe throttle forward          |
    | 0x02            | <reserved>                     |
    | 0x03            | servo channel to use           |
    | 0x04            | reverse throttle flag          |
    | 0x05 - 0x0A     | left, mid, right steering      |
    """

    def __init__(self, proto):
        self.proto = proto
        self.ison = False
        self.eeprom_addr = 0

    async def acquired(self, first):
        pass

    async def on(self):
        self.ison = True

    async def set_steering(self, steering):
        if not self.ison:
            raise RuntimeError('Motors are not turn on; turn them on first.')
        if self.proto.is_charging():
            raise RuntimeError('You may not drive the car while it is charging!')
        steering = int(round(min(max(steering, -45), 45)))
        channel = 1 if (self.proto.eeprom_vals[self.eeprom_addr + 3] != 0) else 0
        left, mid, right = struct.unpack('!HHH', self.proto.eeprom_read_buf(self.eeprom_addr + 5, 6))
        if steering == 0:   # straight
            val = mid
        elif steering < 0:  # right
            val = lerp(steering, -45, 0, right, mid)
        else:               # left
            val = lerp(steering, 0, 45, mid, left)
        val = int(round(val))
        await self.proto.set_steering(val, channel=channel)

    async def set_throttle(self, throttle):
        if not self.ison:
            raise RuntimeError('Motors are not turn on; turn them on first.')
        if self.proto.is_charging():
            raise RuntimeError('You may not drive the car while it is charging!')
        throttle = int(round(min(max(throttle, -100), 100)))
        reverse = (self.proto.eeprom_vals[self.eeprom_addr + 4] == 0)
        await self.proto.set_throttle(-throttle if reverse else throttle)

    async def get_safe_throttle(self):
        min_throttle, max_throttle = struct.unpack('!bb', self.proto.eeprom_read_buf(self.eeprom_addr, 2))
        return min_throttle, max_throttle

    async def set_safe_throttle(self, min_throttle, max_throttle):
        buf = struct.pack('!bb', min_throttle, max_throttle)
        for i, val in enumerate(list(buf)):
            await self.proto.write_eeprom(self.eeprom_addr + i, val)

    async def off(self):
        if self.ison:
            try:
                await self.proto.set_throttle(0)
            finally:
                self.ison = False

    async def released(self, last):
        if last:
            try:
                await self.off()
            except:
                # Well we tried our best.
                pass

    async def swap_motor_direction(self):
        reverse = (self.proto.eeprom_vals[self.eeprom_addr + 4] == 0)
        await self.proto.write_eeprom(self.eeprom_addr + 4, 1 if reverse else 0)

    async def set_servo_channel(self, channel):
        await self.proto.write_eeprom(self.eeprom_addr + 3, 1 if channel else 0)

    async def raw_set_servo(self, val):
        channel = 1 if (self.proto.eeprom_vals[self.eeprom_addr + 3] != 0) else 0
        await self.proto.set_steering(val, channel=channel)

    async def set_servo_params(self, left, mid, right):
        buf = struct.pack('!HHH', left, mid, right)
        addr = self.eeprom_addr + 5
        for i, val in enumerate(list(buf)):
            await self.proto.write_eeprom(addr + i, val)

    def rpc_extra_exports(self):
        return [
            'swap_motor_direction',
            'set_servo_channel',
            'raw_set_servo',
            'set_servo_params',
        ]


class Calibrator(cio.CalibratorIface):
    def __init__(self, _proto):
        pass

    async def acquired(self, first):
        pass

    async def start(self):
        pass  # no-op

    async def status(self):
        pass  # no-op

    async def script_name(self):
        return "calibrate_car_v3"

    async def released(self, last):
        pass


class CarControl(cio.CarControlIface):
    def __init__(self, proto):
        self.proto = proto
        self.ison = False
        # We have a feature to detect when the car is stuck when
        # driving for a certain number of degrees. This is a feature
        # to protect the car so that it doesn't drive *forever* against
        # a wall (or whatever obstacle) and burn itself up. There are
        # two parameters for this features:
        #  - `DEG_HIST_LEN`: how many points of history to keep
        #  - `DEG_HIST_THRESHOLD`: the number of degrees we expect (in
        #                          the worst case) for the car to drive
        #                          within the kept history
        # So, if the car doesn't turn `DEG_HIST_THRESHOLD` within its history
        # of length `DEG_HIST_LEN`, then we stop the car and raise an error.
        self.DEG_HIST_LEN = 50
        self.DEG_HIST_THRESHOLD = 10

    async def acquired(self, first):
        await self.proto.imu_acquire()

    async def on(self):
        self.ison = True

    async def straight(self, throttle, sec=None, cm=None):
        if cm is not None:
            raise ValueError('This device does not have a wheel encoder, thus you may not pass `cm` to travel a specific distance.')

        if sec is None:
            raise ValueError('You must specify `sec`, the number of seconds to drive.')

        motors = CarMotors(self.proto)
        await motors.on()

        try:
            await motors.set_steering(0)
            await asyncio.sleep(0.1)

            start_time = time.time()

            orig_yaw = None

            while self.ison and (time.time() - start_time < sec):
                await self.proto.wait_imu_tick(timeout=0.2)
                _, _, yaw = imu_util.roll_pitch_yaw(tuple(self.proto.quaternion))
                if orig_yaw is None:
                    orig_yaw = yaw
                error = math.radians(yaw - orig_yaw)
                error = math.atan2(math.sin(error), math.cos(error))  # normalize into [-pi, +pi]
                error = math.degrees(error)
                await motors.set_throttle(throttle)
                await motors.set_steering(error if throttle < 0 else -error)

        finally:
            await motors.off()

        await asyncio.sleep(0.1)

    async def drive(self, steering, throttle, sec=None, deg=None):
        if sec is not None and deg is not None:
            raise ValueError('You may not specify both `sec` and `deg`.')

        if sec is None and deg is None:
            raise ValueError('You must specify either `sec` or `deg`.')

        if deg is not None and deg <= 0.0:
            raise ValueError('You must pass `deg` as a postive value.')

        motors = CarMotors(self.proto)
        await motors.on()

        try:
            await motors.set_steering(steering)
            await asyncio.sleep(0.1)

            if sec is not None:
                start_time = time.time()
                while self.ison and (time.time() - start_time < sec):
                    await motors.set_throttle(throttle)
                    await motors.set_steering(steering)
                    await asyncio.sleep(min(0.5, time.time() - start_time))

            else:  # deg is not None
                last_yaw = None
                accum_yaw = 0.0
                history = deque()
                history_accum = 0.0
                while self.ison:
                    await self.proto.wait_imu_tick(timeout=0.2)
                    _, _, yaw = imu_util.roll_pitch_yaw(tuple(self.proto.quaternion))
                    if last_yaw is None:
                        diff = 0.0
                    else:
                        diff = math.radians(yaw - last_yaw)
                        diff = math.atan2(math.sin(diff), math.cos(diff))  # normalize into [-pi, +pi]
                        diff = math.degrees(diff)
                    last_yaw = yaw
                    accum_yaw += diff
                    if abs(accum_yaw) >= deg:
                        break
                    await motors.set_throttle(throttle)
                    await motors.set_steering(steering)
                    history.append(diff)
                    history_accum += diff
                    while len(history) > self.DEG_HIST_LEN:
                        old_diff = history.popleft()
                        history_accum -= old_diff
                    if len(history) == self.DEG_HIST_LEN and abs(history_accum) < self.DEG_HIST_THRESHOLD:
                        raise RuntimeError('Not making progress; is the car stuck somewhere?')

        finally:
            await motors.off()

        await asyncio.sleep(0.1)

    async def off(self):
        self.ison = False

    async def released(self, last):
        await self.off()
        await self.proto.imu_release()

