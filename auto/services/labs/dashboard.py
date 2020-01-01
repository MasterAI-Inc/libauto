###############################################################################
#
# Copyright (c) 2017-2018 AutoAuto, LLC
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from AutoAuto, LLC.
#
###############################################################################

import os
import uuid
import asyncio
import itertools
import subprocess

import auto
from auto.camera import draw_frame_index, base64_encode_image
from auto.inet import Wireless, list_wifi_ifaces, get_ip_address

from auto import logger
log = logger.init(__name__, terminal=True)

from util import shutdown, update_libauto


class Dashboard:

    def __init__(self, camera, controller):
        self.wireless = Wireless(list_wifi_ifaces()[0])   # TODO
        self.capture_streams = {}
        self.camera = camera
        self.controller = controller

    async def connected_cdp(self):
        pass

    async def new_user_session(self, username, user_session):
        pass

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
        await self._stop_capture_stream(user_session)

    async def disconnected_cdp(self):
        pass   # we do all the cleanup in `end_user_session`

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
            response = await self.shutdown(reboot=False)
        elif command == 'reboot':
            response = await self.shutdown(reboot=True)
        elif command == 'update_libauto':
            response = await self.update_libauto()
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
        if component == 'version':
            return await self._get_version()
        elif component == 'version_controller':
            return await self._get_cio_version()
        elif component == 'wifi_ssid':
            return self.wireless.current()  # TODO
        elif component == 'wifi_iface':
            return self.wireless.interface  # TODO
        elif component == 'local_ip_addr':
            return get_ip_address(self.wireless.interface)  # TODO
        elif component == 'capture_one_frame':
            return await self._capture_one_frame(query_id, send_func, user_session)
        else:
            return 'unsupported'

    async def _capture_one_frame(self, query_id, send_func, user_session):
        guid = str(uuid.uuid4())
        async def run():
            frame = await self.camera.capture()
            base64_img = base64_encode_image(frame)
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
            return False
        guid = str(uuid.uuid4())
        async def run():
            try:
                for index in itertools.count():
                    frame = await self.camera.capture()
                    draw_frame_index(frame, index)
                    base64_img = base64_encode_image(frame)
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

    async def _get_version(self):
        return auto.__version__

    async def _get_cio_version(self):
        cio_version_iface = await self.controller.acquire('VersionInfo')
        cio_version = await cio_version_iface.version()
        cio_version = '.'.join([str(v) for v in cio_version])
        await self.controller.release(cio_version_iface)
        return cio_version

