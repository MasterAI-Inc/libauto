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
import sys
import random
import asyncio
from websockets import connect as ws_connect
from websockets import WebSocketException

from auto import __version__ as libauto_version

from auto.services.controller.client import CioRoot
from auto.services.camera.client import CameraRGB
from auto.services.console.client import CuiRoot

from auto import logger
log = logger.init('labs connection', terminal=True)

from pty_manager import PtyManager
from verification_method import Verification
from dashboard import Dashboard
from proxy import Proxy


BASE_PROTO = os.environ.get('LABS_PROTO', 'wss')
BASE_HOST  = os.environ.get('LABS_HOST', 'ws.autoauto.ai')
BASE_URL = "{}://{}/autopair/device".format(BASE_PROTO, BASE_HOST)


async def run(ws, consumers):
    while True:
        msg = await ws.recv()

        try:
            msg = json.loads(msg)
        except:
            # Bad message!
            log.error('Got bad JSON message: {}'.format(repr(msg)))
            continue

        print(msg)

        if 'ping' in msg:
            self.send({'pong': True})
            continue

        if 'origin' in msg:
            if msg['origin'] == 'server' and 'connect' in msg and msg['connect'] == 'user':
                username = msg['username']
                user_session = msg['user_session']
                if self.add_user_with_session(username, user_session):
                    for c in self.consumers:
                        c.new_user_session(username, user_session)
            elif msg['origin'] == 'server' and 'disconnect' in msg and msg['disconnect'] == 'user':
                username = msg['username']
                user_session = msg['user_session']
                if self.remove_user_with_session(username, user_session):
                    for c in self.consumers:
                        c.end_user_session(username, user_session)

            elif msg['origin'] == 'server' and 'hello' in msg:
                info = msg['yourinfo']
                vin = info['vin']
                name = info['name']
                description = info['description']  # <-- Where should we display this?
                print_all('Device Name: {}'.format(name))
                print_all('Device VIN:  {}'.format(vin))
                output = set_hostname(name)
                log.info("Set hostname, output is: {}".format(output))

        for c in self.consumers:
            c.got_message(msg, self.smart_send)


async def run_forever():
    system_up_user = sys.argv[1]   # the "UnPrivileged" system user

    controller = CioRoot()
    camera = CameraRGB()
    console = CuiRoot()

    await controller.init()
    await camera.connect()
    await console.init()

    cio_version_iface = await controller.acquire('VersionInfo')
    cio_version = await cio_version_iface.version()
    await controller.release(cio_version_iface)

    log.info("Will run the PTY manager using the unprivileged user: {}".format(system_up_user))
    log.info("Libauto version:    {}".format(libauto_version))
    log.info("Controller version: {}".format(cio_version))

    await console.clear_text()
    await console.write_text("Libauto version:    {}\n".format(libauto_version))
    await console.write_text("Controller version: {}\n".format(cio_version))

    auth = await controller.acquire('Credientials')
    was_missing = False
    while True:
        token = await auth.get_token()
        if token:
            if was_missing:
                await console.write_text("The token is now set!")
            break
        else:
            if not was_missing:
                await console.write_text("Token not yet set...")
                was_missing = True
            await asyncio.sleep(2)

    url = BASE_URL + '/' + token

    consumers = [
        PtyManager(system_up_user, console),
        Verification(console),
        Dashboard(camera, controller),
        Proxy(),
    ]

    while True:
        try:
            async with ws_connect(url) as ws:
                await run(ws, consumers)
        except WebSocketException as e:
            log.info('Connection closed: {}'.format(e))
        except Exception as e:
            log.info('Unknown error: {}'.format(e))
        finally:
            reconnect_delay_seconds = lambda: (10 + random.randint(2, 8))
            await asyncio.sleep(reconnect_delay_seconds)


if __name__ == '__main__':
    asyncio.run(run_forever())

