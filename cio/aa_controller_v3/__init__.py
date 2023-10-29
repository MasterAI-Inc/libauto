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

from auto.buzzer_lang import BuzzParser

import cio

from .proto import Proto
from .db import default_db
from .battery_discharge_curve import battery_map_millivolts_to_percentage
from .camera_async import CameraRGB_Async
from .camera_pi import CameraRGB

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
            'Power': Power,
            'Buzzer': Buzzer,
            #'Gyroscope': Gyroscope,
            #'Gyroscope_accum': GyroscopeAccum,
            #'Accelerometer': Accelerometer,
            #'Magnetometer': Magnetometer,
            #'AHRS': Ahrs,
            #'PushButtons': PushButtons,
            #'LEDs': LEDs,
            #'Encoders': Encoders,
            #'CarMotors': CarMotors,
            #'PID_steering': PidSteering,
            #'CarControl': CarControl,
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
                v = VersionInfo(self.proto)
                await v.acquired(first=True)
                try:
                    major, minor = await v.version()
                    if major != 3:
                        raise Exception('Controller is not version 3, thus this interface will not work.')
                finally:
                    try:
                        await v.released(last=True)
                    except:
                        pass  # we did the best we could
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


class Power(cio.PowerIface):
    def __init__(self, proto):
        self.proto = proto

    async def acquired(self, first):
        pass

    async def state(self):
        vbatt1, vbatt2, vchrg = self.proto.voltages
        return 'battery' if vbatt2 >= vchrg else 'charging'

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

    async def acquired(self, first):
        pass

    async def is_currently_playing(self):
        return Buzzer._is_playing or self.proto.buzzer_is_playing

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
        try:
            for freqHz, durationMS, _volume in note_tuples:
                await self.proto.play(freqHz, durationMS)
        finally:
            Buzzer._is_playing = False

    async def released(self, last):
        pass

