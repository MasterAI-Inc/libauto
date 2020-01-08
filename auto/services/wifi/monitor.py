###############################################################################
#
# Copyright (c) 2017-2020 Master AI, Inc.
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from Master AI, Inc.
#
###############################################################################

from auto.services.camera.client import CameraRGB
from auto.services.console.client import CuiRoot
from auto.services.controller.client import CioRoot
from auto.services.labs.util import update_libauto
from auto.services.wifi import myzbarlight
from auto.services.wifi import util

from auto.inet import Wireless, list_wifi_ifaces, get_ip_address, has_internet_access

import itertools
import asyncio
import json
import cv2
import sys
import os

from auto import logger
log = logger.init(__name__, terminal=True)


NUM_INTERNET_ATTEMPTS = 5
INTERNET_ATTEMPT_SLEEP = 4


async def _has_internet_access_multi_try():
    loop = asyncio.get_running_loop()

    for i in range(NUM_INTERNET_ATTEMPTS-1):
        success = await loop.run_in_executor(None, has_internet_access)
        if success:
            return True
        log.info("Check for internet FAILED.")
        await asyncio.sleep(INTERNET_ATTEMPT_SLEEP)

    success = await loop.run_in_executor(None, has_internet_access)
    if success:
        return True

    log.info("Check for internet FAILED last attempt. Concluding there is no internet access.")
    return False


async def _stream_frame(frame, console):
    if frame.ndim == 2:
        height, width = frame.shape
        channels = 1
    elif frame.ndim == 3:
        height, width, channels = frame.shape
    else:
        return  # :(
    shape = [width, height, channels]
    rect = [22, 20, width, height]
    await console.stream_image(rect, shape, frame.tobytes())


async def _current(wireless):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, wireless.current)


async def _get_wifi_info_from_user(wireless, console):
    loop = asyncio.get_running_loop()

    camera = CameraRGB()
    await camera.connect()

    for i in itertools.count():
        frame = await camera.capture()
        frame = await loop.run_in_executor(None, cv2.cvtColor, frame, cv2.COLOR_RGB2GRAY)
        await _stream_frame(frame, console)
        qrcodes = await loop.run_in_executor(None, myzbarlight.qr_scan, frame)

        if len(qrcodes) > 0:
            qr_data = qrcodes[0]
            try:
                qr_data = json.loads(qr_data.decode('utf-8'))
                ssid = qr_data['s']
                password = qr_data['p']
                break
            except:
                # We got invalid data from the QR code, which is
                # fine, we'll just move on with life and try again.
                pass

        if (i % 100) == 99:
            # Every 100 frames, we'll check to see if WiFi magically came back.
            if (await _current(wireless)) is not None:
                ssid = None
                password = None
                break

    await console.clear_image()
    await camera.close()

    return ssid, password


async def _get_labs_auth_code(controller):
    auth = await controller.acquire('Credentials')
    auth_code = await auth.get_labs_auth_code()
    await controller.release(auth)
    return auth_code


async def _store_labs_auth_code(controller, auth_code):
    auth = await controller.acquire('Credentials')
    did_save = await auth.set_labs_auth_code(auth_code)
    await controller.release(auth)
    return did_save


async def _store_jupyter_password(controller, jupyter_password):
    auth = await controller.acquire('Credentials')
    did_save = await auth.set_jupyter_password(jupyter_password)
    await controller.release(auth)
    return did_save


async def _ensure_token(console, controller, system_priv_user):
    loop = asyncio.get_running_loop()

    auth_code = await _get_labs_auth_code(controller)

    if auth_code is not None:
        # We have an auth code which means this device was set with a token already. All is well.
        return

    await console.big_image('token_error')
    await console.big_status('Ready to receive login token.')

    camera = CameraRGB()
    await camera.connect()

    system_password = None

    for i in itertools.count():
        frame = await camera.capture()
        frame = await loop.run_in_executor(None, cv2.cvtColor, frame, cv2.COLOR_RGB2GRAY)
        await _stream_frame(frame, console)
        qrcodes = await loop.run_in_executor(None, myzbarlight.qr_scan, frame)

        if len(qrcodes) > 0:
            qr_data = qrcodes[0]
            try:
                qr_data = json.loads(qr_data.decode('utf-8'))
                token = qr_data['t']
                if 'p' in qr_data:
                    # This allows us to override the default system_password for special-purpose devices.
                    # The default is just... a default. No matter what is set here, it can be changed later.
                    system_password = qr_data['p']
                break
            except:
                pass

    await camera.close()
    await console.clear_image()

    await console.big_image('token_success')
    await console.big_status('Success. Token: {}...'.format(token[:4]))

    await console.write_text("Received token: {}...\n".format(token[:4]))

    if system_password is None:
        # If a particular default system_password was not specified, we will generate a good
        # default system_password from the token. This is a good thing, since it ensures that
        # each device is given a strong, unique default system_password.
        system_password = util.derive_system_password(token)

    jupyter_password = util.derive_jupyter_password(token)
    auth_code = util.derive_labs_auth_code(token)

    if await util.change_system_password(system_priv_user, system_password):
        await console.write_text("Successfully changed {}'s password!\n".format(system_priv_user))
    else:
        await console.write_text("Failed to change {}' password.\n".format(system_priv_user))

    if await _store_jupyter_password(controller, jupyter_password):
        await console.write_text("Stored Jupyter password: {}...\n".format(jupyter_password[:4]))
    else:
        await console.write_text("Failed to store Jupyter password.\n")

    if await _store_labs_auth_code(controller, auth_code):
        await console.write_text("Stored Labs Auth Code: {}...\n".format(auth_code[:4]))
    else:
        await console.write_text("Failed to store Labs Auth Code.\n")

    await asyncio.sleep(2)

    await console.big_clear()


async def _update_and_reboot_if_no_token(controller):
    if (await _get_labs_auth_code(controller)) is None:
        log.info("We now have Wifi, but we doesn't yet have a token. Therefore we will take this opportunity to update libauto.")
        return await update_libauto()


async def _print_connection_info(wireless, console):
    loop = asyncio.get_running_loop()

    iface = wireless.interface
    await console.write_text("WiFi interface name: {}\n".format(iface))

    current = await _current(wireless)
    await console.write_text("Connected to WiFi SSID: {}\n".format(current))

    if iface and current:
        ip_address = await loop.run_in_executor(None, get_ip_address, iface)
        await console.write_text("Current IP address: {}\n".format(ip_address))


async def _main_loop(wireless, console, controller, system_priv_user):
    loop = asyncio.get_running_loop()

    last_wifi_seen = None
    confident_about_token = False

    # Repeat forever: Check to see if we are connected to WiFi. If not, wait 10 seconds
    #                 to see if anything changes. If after 10 seconds we still don't have
    #                 WiFi, initiate the WiFi connection screen. If we _do_ have WiFi, then
    #                 we'll repeat this whole process after 5 seconds.
    while True:
        current = await _current(wireless)
        if current != last_wifi_seen:
            log.info("Current WiFi network: {}".format(current))
            last_wifi_seen = current

        if current is None:
            log.info("No WiFi!")
            await asyncio.sleep(10)
            if (await _current(wireless)) is None:
                log.info("Still no WiFi after 10 seconds... will ask user to connect.")
                await console.big_image('wifi_error')
                await console.big_status('https://labs.autoauto.ai/wifi')
                while (await _current(wireless)) is None:
                    ssid, password = await _get_wifi_info_from_user(wireless, console)
                    if ssid is None:
                        log.info("WiFi magically came back before user input.")
                        break
                    log.info("Will try to connect to SSID: {}".format(ssid))
                    await console.big_image('wifi_pending')
                    await console.big_status('Trying to connect...')
                    did_connect = await loop.run_in_executor(None, wireless.connect, ssid, password)
                    has_internet = (await _has_internet_access_multi_try()) if did_connect else False
                    if not did_connect or not has_internet:
                        if did_connect:
                            await loop.run_in_executor(None, wireless.delete_connection, ssid)
                            msg = 'Connected to WiFi...\nbut no internet detected.\nPlease use another network.'
                        else:
                            msg = 'WiFi credentials did not work.\nDid you type them correctly?\nPlease try again.'
                        log.info(msg)
                        await console.big_image('wifi_error')
                        await console.big_status(msg)
                    else:
                        log.info("Success! Connected to SSID: {}".format(ssid))
                        await console.big_image('wifi_success')
                        await console.big_status('WiFi connection success!')
                        await asyncio.sleep(5)
                        await _print_connection_info(wireless, console)
                        break
                await console.big_clear()

                update_result = await _update_and_reboot_if_no_token(controller)
                if update_result is not None:
                    log.info('Attempted to update libauto, got response: {}'.format(update_result))

        else:
            # We have WiFi.
            # After WiFi, we care that we have a Token so that we can authenticate with the CDP.
            if not confident_about_token:
                await _ensure_token(console, controller, system_priv_user)
                confident_about_token = True
                log.info('Ensured token.')

        await asyncio.sleep(5)


async def run_forever(system_priv_user):
    loop = asyncio.get_running_loop()

    log.info("Starting Wifi controller using the privileged user: {}".format(system_priv_user))

    wifi_interface = await loop.run_in_executor(None, list_wifi_ifaces)
    wifi_interface = wifi_interface[0]

    wireless = Wireless(wifi_interface)

    console = CuiRoot()
    controller = CioRoot()

    await console.init()
    await controller.init()

    await _print_connection_info(wireless, console)

    await _main_loop(wireless, console, controller, system_priv_user)


async def _mock_wifi_run_forever(system_priv_user):
    loop = asyncio.get_running_loop()

    log.info("Starting Mock Wifi controller!!!")

    class MockWireless:
        def __init__(self, interface):
            self.interface = interface
            self.curr = None
            self.fail_count = 2

        def connect(self, ssid, password):
            log.info('Calling Mock Wireless: connect({}, {})'.format(repr(ssid), repr(password)))
            if self.fail_count > 0:
                self.fail_count -= 1
                return False
            self.curr = ssid
            return True

        def current(self):
            log.info('Calling Mock Wireless: current()')
            return self.curr

        def delete_connection(self, ssid_to_delete):
            log.info('Calling Mock Wireless: delete_connection({})'.format(repr(ssid_to_delete)))
            if ssid_to_delete == self.curr:
                self.curr = None

    wifi_interface = await loop.run_in_executor(None, list_wifi_ifaces)
    wifi_interface = wifi_interface[0]

    wireless = MockWireless(wifi_interface)

    console = CuiRoot()
    controller = CioRoot()

    await console.init()
    await controller.init()

    await _print_connection_info(wireless, console)

    await _main_loop(wireless, console, controller, system_priv_user)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        system_priv_user = sys.argv[1]   # the "Privileged" system user
    else:
        system_priv_user = os.environ['USER']

    #asyncio.run(_mock_wifi_run_forever(system_priv_user))
    asyncio.run(run_forever(system_priv_user))

