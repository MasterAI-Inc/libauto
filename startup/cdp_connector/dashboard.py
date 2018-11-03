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
import subprocess
from queue import Queue, Empty
from threading import Thread

from auto.camera_rpc_client import CameraRGB
from auto.camera import wrap_frame_index_decorator, base64_encode_image
from auto.inet import Wireless, get_ip_address

from auto import logger
log = logger.init(__name__, terminal=True)


class Dashboard:

    def __init__(self):
        self.wireless = Wireless('wlan0')
        self.capture_streams = {}

    def connected_cdp(self):
        pass

    def new_user_session(self, username, user_session):
        pass

    def got_message(self, msg, send_func):
        if 'origin' in msg and msg['origin'] == 'user' and 'type' in msg:
            if msg['type'] == 'query':
                self._query(msg['components'], msg['query_id'], msg['user_session'], send_func)
            elif msg['type'] == 'command':
                self._command(msg['command'], msg['command_id'], msg['user_session'], send_func)

    def end_user_session(self, username, user_session):
        self._stop_capture_stream(user_session)

    def disconnected_cdp(self):
        user_sessions = list(self.capture_streams.keys())
        for us in user_sessions:
            self._stop_capture_stream(us)

    def _query(self, components, query_id, user_session, send_func):
        response = {}
        for c in components:
            response[c] = self._query_component(c, query_id, send_func, user_session)
        send_func({
            'type': 'query_response',
            'query_id': query_id,
            'response': response,
            'to_user_session': user_session,
        })

    def _command(self, command, command_id, user_session, send_func):
        if command == 'shutdown':
            response = self._shutdown(reboot=False)
        elif command == 'reboot':
            response = self._shutdown(reboot=True)
        elif command == 'update_libauto':
            response = self._update_libauto()
        elif command == 'start_capture_stream':
            response = self._start_capture_stream(command_id, send_func, user_session)
        elif command == 'stop_capture_stream':
            response = self._stop_capture_stream(user_session)
        else:
            return
        send_func({
            'type': 'command_response',
            'command_id': command_id,
            'response': response,
            'to_user_session': user_session,
        })

    def _query_component(self, component, query_id, send_func, user_session):
        if component == 'version':
            return self._get_version()
        elif component == 'wifi_ssid':
            return self.wireless.current()
        elif component == 'wifi_iface':
            return self.wireless.interface()
        elif component == 'local_ip_addr':
            return get_ip_address(self.wireless.interface())
        elif component == 'capture_one_frame':
            return self._capture_one_frame(query_id, send_func, user_session)
        else:
            return 'unsupported'

    def _capture_one_frame(self, query_id, send_func, user_session):
        guid = str(uuid.uuid4())
        def run():
            camera = CameraRGB()
            frame = camera.capture()
            base64_img = base64_encode_image(frame)
            send_func({
                'type': 'query_response_async',
                'query_id': query_id,
                'async_guid': guid,
                'response': {'base64_img': base64_img},
                'to_user_session': user_session,
            })
            camera.close()
        Thread(target=run).start()
        return guid

    def _start_capture_stream(self, command_id, send_func, user_session):
        if user_session in self.capture_streams:
            return False
        guid = str(uuid.uuid4())
        queue = Queue()
        self.capture_streams[user_session] = queue
        def run():
            camera = wrap_frame_index_decorator(CameraRGB())
            while True:
                frame = camera.capture()
                base64_img = base64_encode_image(frame)
                send_func({
                    'type': 'command_response_async',
                    'command_id': command_id,
                    'async_guid': guid,
                    'response': {'base64_img': base64_img},
                    'to_user_session': user_session,
                })
                try:
                    g = queue.get(timeout=0.1)
                    if g is False:
                        break
                except Empty:
                    pass
            camera.close()
        Thread(target=run).start()
        return guid

    def _stop_capture_stream(self, user_session):
        if user_session not in self.capture_streams:
            return False
        queue = self.capture_streams[user_session]
        del self.capture_streams[user_session]
        queue.put(False)
        return True

    def _shutdown(self, reboot):
        cmd = 'reboot' if reboot else 'poweroff'
        cmd = cmd.split(' ')
        output = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.decode('utf-8')
        return output

    def _update_libauto(self):
        cmd = ['update_libauto']
        log.info("Will update libauto!!!")
        output = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.decode('utf-8')
        return output

    def _get_version(self):
        path = os.path.realpath(__file__)
        for _ in range(3):
            path = os.path.dirname(path)
        with open(os.path.join(path, 'version.txt'), 'r') as f:
            return f.read().strip()

