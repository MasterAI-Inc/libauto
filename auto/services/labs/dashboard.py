###############################################################################
#
# Copyright (c) 2017-2020 Master AI, Inc.
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from Master AI, Inc.
#
###############################################################################

import uuid
import asyncio
import itertools

import auto
from auto.camera import draw_frame_index, base64_encode_image
from auto.inet import Wireless, list_wifi_ifaces, get_ip_address

from auto import logger
log = logger.init(__name__, terminal=True)

from auto.services.labs.util import shutdown, update_libauto


class Dashboard:

    def __init__(self, camera, controller):
        self.wireless = None
        self.capture_streams = {}
        self.camera = camera
        self.controller = controller

    async def init(self):
        loop = asyncio.get_running_loop()
        wifi_ifaces = await loop.run_in_executor(None, list_wifi_ifaces)
        self.wireless = Wireless(wifi_ifaces[0])

    async def connected_cdp(self):
        self.known_user_sessions = set()

    async def new_user_session(self, username, user_session):
        self.known_user_sessions.add(user_session)

    async def got_message(self, msg, send_func):
        if 'origin' in msg and msg['origin'] == 'user' and 'type' in msg:
            type_ = msg['type']

            if type_ == 'query':
                components = msg['components']
                query_id = msg['query_id']
                user_session = msg['user_session']
                coro = self._query(components, query_id, user_session, send_func)

            elif type_ == 'command':
                command = msg['command']
                command_id = msg['command_id']
                user_session = msg['user_session']
                coro = self._command(command, command_id, user_session, send_func)

            else:
                return

            asyncio.create_task(coro)

    async def end_user_session(self, username, user_session):
        self.known_user_sessions.remove(user_session)
        await self._stop_capture_stream(user_session)

    async def disconnected_cdp(self):
        self.known_user_sessions = set()

    async def _query(self, components, query_id, user_session, send_func):
        response = {}
        for c in components:
            response[c] = await self._query_component(c, query_id, send_func, user_session)
        await send_func({
            'type': 'query_response',
            'query_id': query_id,
            'response': response,
            'to_user_session': user_session,
        })

    async def _command(self, command, command_id, user_session, send_func):
        if command == 'shutdown':
            response = await shutdown(reboot=False)
        elif command == 'reboot':
            response = await shutdown(reboot=True)
        elif command == 'update_libauto':
            response = await update_libauto()
        elif command == 'start_capture_stream':
            response = await self._start_capture_stream(command_id, send_func, user_session)
        elif command == 'stop_capture_stream':
            response = await self._stop_capture_stream(user_session)
        else:
            return
        await send_func({
            'type': 'command_response',
            'command_id': command_id,
            'response': response,
            'to_user_session': user_session,
        })

    async def _query_component(self, component, query_id, send_func, user_session):
        loop = asyncio.get_running_loop()
        if component == 'version':
            return auto.__version__
        elif component == 'version_controller':
            return await self._get_cio_version()
        elif component == 'wifi_ssid':
            return await loop.run_in_executor(None, self.wireless.current)
        elif component == 'wifi_iface':
            return self.wireless.interface
        elif component == 'local_ip_addr':
            return await loop.run_in_executor(None, get_ip_address, self.wireless.interface)
        elif component == 'battery_state':
            return await self._get_battery_state()
        elif component == 'capture_one_frame':
            return await self._capture_one_frame(query_id, send_func, user_session)
        else:
            return 'unsupported'

    async def _capture_one_frame(self, query_id, send_func, user_session):
        guid = str(uuid.uuid4())
        async def run():
            loop = asyncio.get_running_loop()
            frame = await self.camera.capture()
            base64_img = await loop.run_in_executor(None, base64_encode_image, frame)
            await send_func({
                'type': 'query_response_async',
                'query_id': query_id,
                'async_guid': guid,
                'response': {'base64_img': base64_img},
                'to_user_session': user_session,
            })
        asyncio.create_task(run())
        return guid

    async def _start_capture_stream(self, command_id, send_func, user_session):
        if user_session in self.capture_streams:
            # A single user session needs at most one camera stream.
            return False
        if user_session not in self.known_user_sessions:
            # This isn't a security issue; it's a race condition issue.
            # Because this method is run as a task, it's possible this method
            # is running after we receive notice the user has disconnected.
            # Thus, this check prevents creating a stream which will stream
            # to no-one and will never halt.
            return False
        guid = str(uuid.uuid4())
        async def run():
            try:
                loop = asyncio.get_running_loop()
                for index in itertools.count():
                    frame = await self.camera.capture()
                    await loop.run_in_executor(None, draw_frame_index, frame, index)
                    base64_img = await loop.run_in_executor(None, base64_encode_image, frame)
                    await send_func({
                        'type': 'command_response_async',
                        'command_id': command_id,
                        'async_guid': guid,
                        'response': {'base64_img': base64_img},
                        'to_user_session': user_session,
                    })
            except asyncio.CancelledError:
                pass
        task = asyncio.create_task(run())
        self.capture_streams[user_session] = task
        return guid

    async def _stop_capture_stream(self, user_session):
        if user_session not in self.capture_streams:
            return False
        task = self.capture_streams[user_session]
        del self.capture_streams[user_session]
        task.cancel()
        await task
        return True

    async def _get_cio_version(self):
        cio_version_iface = await self.controller.acquire('VersionInfo')
        cio_version = await cio_version_iface.version()
        cio_version = '.'.join([str(v) for v in cio_version])
        await self.controller.release(cio_version_iface)
        return cio_version

    async def _get_battery_state(self):
        battery = await self.controller.acquire('BatteryVoltageReader')
        minutes, percentage = await battery.minutes()
        await self.controller.release(battery)
        return {
            'minutes': minutes,
            'percentage': percentage,
        }

