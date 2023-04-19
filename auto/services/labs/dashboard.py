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
import numpy as np

import auto
from auto.camera import draw_frame_index, base64_encode_image
from auto.inet import Wireless, list_wifi_ifaces, get_ip_address, get_mac_address

from auto import logger
log = logger.init(__name__, terminal=True)

from auto.services.labs.util import update_libauto


class Dashboard:

    def __init__(self, controller, capabilities):
        self.wireless = None
        self.mac_address = None
        self.capture_streams = {}
        self.controller = controller
        self.capabilities = capabilities

    async def init(self):
        loop = asyncio.get_running_loop()
        self.power = await self.controller.acquire('Power')
        self.camera = await self.controller.acquire('Camera')
        wifi_ifaces = await loop.run_in_executor(None, list_wifi_ifaces)
        if wifi_ifaces:
            wifi_iface = wifi_ifaces[0]
            self.wireless = Wireless(wifi_iface)
            self.mac_address = await loop.run_in_executor(None, get_mac_address, wifi_iface)
        if 'PhysicsClient' in self.capabilities:
            self.physics = await self.controller.acquire('PhysicsClient')
        else:
            self.physics = None

    async def connected_cdp(self):
        self.known_user_sessions = set()

    async def new_device_session(self, vin):
        pass

    async def new_user_session(self, username, user_session):
        self.known_user_sessions.add(user_session)

    async def got_message(self, msg, send_func):
        if 'origin' in msg and 'type' in msg:
            origin = msg['origin']
            type_ = msg['type']

            if origin == 'user':
                await self._handle_user_message(msg, send_func, type_)
            elif origin == 'server':
                await self._handle_server_message(msg, send_func, type_)

    async def _handle_user_message(self, msg, send_func, type_):
        if type_ == 'query':
            components = msg['components']
            query_id = msg['query_id']
            user_session = msg['user_session']
            coro = self._query(components, query_id, user_session, send_func)

        elif type_ == 'command':
            command = msg['command']
            command_id = msg['command_id']
            user_session = msg['user_session']
            coro = self._command(command, command_id, user_session, send_func, msg)

        else:
            return

        asyncio.create_task(coro)

    async def _handle_server_message(self, msg, send_func, type_):
        if type_ == 'query_device_info':
            coro = self._send_device_info_to_server(send_func)

        elif type_ == 'command':
            command = msg['command']
            command_id = msg['command_id']
            coro = self._server_command(command, command_id, send_func, msg)

        else:
            return

        asyncio.create_task(coro)

    async def _send_device_info_to_server(self, send_func):
        await send_func({
            'type': 'device_info_response',
            'response': {
                'version': auto.__version__,
                'version_controller': await self._get_cio_version(),
                'mac_address': self.mac_address,
            },
            'target': 'server',
        })

    async def end_device_session(self, vin):
        pass

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

    async def _server_command(self, command, command_id, send_func, msg):
        if command == 'physics_control':
            if self.physics is not None:
                response = await self.physics.control(msg.get('payload'))
            else:
                response = None
        else:
            return
        await send_func({
            'type': 'command_response',
            'command_id': command_id,
            'response': response,
        })

    async def _command(self, command, command_id, user_session, send_func, msg):
        if command == 'shutdown':
            response = await self.power.shut_down()
        elif command == 'reboot':
            response = await self.power.reboot()
        elif command == 'update_libauto':
            response = await update_libauto()
        elif command == 'start_capture_stream':
            response = await self._start_capture_stream(command_id, send_func, user_session)
        elif command == 'stop_capture_stream':
            response = await self._stop_capture_stream(user_session)
        elif command == 'physics_control':
            if self.physics is not None:
                response = await self.physics.control(msg.get('payload'))
            else:
                response = None
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
            if self.wireless:
                return await loop.run_in_executor(None, self.wireless.current)
            else:
                return None
        elif component == 'wifi_iface':
            if self.wireless:
                return self.wireless.interface
            else:
                return None
        elif component == 'local_ip_addr':
            if self.wireless:
                return await loop.run_in_executor(None, get_ip_address, self.wireless.interface)
            else:
                return None
        elif component == 'mac_address':
            return self.mac_address
        elif component == 'battery_state':
            return await self._get_battery_state()
        elif component == 'capture_one_frame':
            return await self._capture_one_frame(query_id, send_func, user_session)
        elif component == 'list_caps':
            return self.capabilities
        else:
            return 'unsupported'

    async def _capture_one_frame(self, query_id, send_func, user_session):
        guid = str(uuid.uuid4())
        async def run():
            loop = asyncio.get_running_loop()
            buf, shape = await self.camera.capture()
            frame = np.frombuffer(buf, dtype=np.uint8).reshape(shape)
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
                    buf, shape = await self.camera.capture()
                    frame = np.frombuffer(buf, dtype=np.uint8).reshape(shape)
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
        minutes, percentage = await self.power.estimate_remaining()
        return {
            'minutes': minutes,
            'percentage': percentage,
        }

