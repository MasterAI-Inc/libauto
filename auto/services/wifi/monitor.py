###############################################################################
#
# Copyright (c) 2017-2018 AutoAuto, LLC
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from AutoAuto, LLC.
#
###############################################################################

from auto.camera_rpc_client import CameraRGB
from auto.inet import Wireless, list_wifi_ifaces, get_ip_address, has_internet_access
from auto.db import secure_db
from auto import print_all
from auto import console

import myzbarlight
import util

import subprocess
import json
import time
import cv2
import sys

from auto import logger
log = logger.init('wifi_controller', terminal=True)


NUM_INTERNET_ATTEMPTS = 5
INTERNET_ATTEMPT_SLEEP = 4


STORE = secure_db()

wireless = Wireless(list_wifi_ifaces()[0])


system_priv_user = sys.argv[1]   # the "Privileged" system user

log.info("Starting Wifi controller using the privileged user: {}".format(system_priv_user))


def has_internet_access_multi_try():
    for i in range(NUM_INTERNET_ATTEMPTS-1):
        if has_internet_access():
            return True
        log.info("Check for internet FAILED.")
        time.sleep(INTERNET_ATTEMPT_SLEEP)
    if has_internet_access():
        return True
    log.info("Check for internet FAILED last attempt. Concluding there is no internet access.")
    return False


def stream_frame(frame):
    if frame.ndim == 2:
        height, width = frame.shape
        channels = 1
    elif frame.ndim == 3:
        height, width, channels = frame.shape
    else:
        return  # :(
    shape = [width, height, channels]
    rect = [22, 20, width, height]
    console.stream_image(rect, shape, frame.tobytes())


def get_wifi_info_from_user():
    camera = CameraRGB()

    for i, frame in enumerate(camera.stream()):
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        stream_frame(frame)
        qrcodes = myzbarlight.qr_scan(frame)

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
            if wireless.current() is not None:
                ssid = None
                password = None
                break

    console.clear_image()
    camera.close()

    return ssid, password


def update_and_reboot_if_no_token():
    token = STORE.get('DEVICE_TOKEN', None)

    if token is None:
        log.info("We now have Wifi, but we doesn't yet have a token. Therefore we will take this opportunity to update libauto.")
        cmd = ['update_libauto']
        output = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.decode('utf-8')


def ensure_token():
    token = STORE.get('DEVICE_TOKEN', None)

    if token is not None:
        # We have a token. All is well.
        return

    console.big_image('images/token_error.png')
    console.big_status('Ready to receive login token.')

    camera = CameraRGB()

    system_password = None

    for i, frame in enumerate(camera.stream()):
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        stream_frame(frame)
        qrcodes = myzbarlight.qr_scan(frame)

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

    console.clear_image()
    camera.close()

    console.big_image('images/token_success.png')
    console.big_status('Success. Token: {}...'.format(token[:5]))

    STORE.put('DEVICE_TOKEN', token)
    print_all("Stored Device token: {}...".format(token[:5]))

    jupyter_password = util.token_to_jupyter_password(token)
    STORE.put('DEVICE_JUPYTER_PASSWORD', jupyter_password)
    print_all("Stored Jupyter password: {}...".format(jupyter_password[:2]))

    if system_password is None:
        # If a particular default system_password was not specified, we will generate a good
        # default system_password from the token. This is a good thing, since it ensures that
        # each device is given a strong, unique default system_password.
        system_password = util.token_to_system_password(token)

    util.change_system_password(system_priv_user, system_password)
    print_all("Successfully changed {}'s password!".format(system_priv_user))

    time.sleep(2)

    console.big_clear()


def print_connection_info():
    iface = wireless.interface
    print_all("WiFi interface name: {}".format(iface))

    current = wireless.current()
    print_all("Connected to WiFi SSID: {}".format(current))

    if iface and current:
        print_all("Current IP address: {}".format(get_ip_address(iface)))


print_connection_info()


# Repeat forever: Check to see if we are connected to WiFi. If not, wait 10 seconds
#                 to see if anything changes. If after 10 seconds we still don't have
#                 WiFi, initiate the WiFi connection screen. If we _do_ have WiFi, then
#                 we'll repeat this whole process after 5 seconds.
while True:
    current = wireless.current()
    log.info("Current WiFi network: {}".format(current))

    if current is None:
        log.info("No WiFi!")
        time.sleep(10)
        if wireless.current() is None:
            log.info("Still no WiFi after 10 seconds... will ask user to connect.")
            console.big_image('images/wifi_error.png')
            console.big_status('https://labs.autoauto.ai/wifi')
            while wireless.current() is None:
                ssid, password = get_wifi_info_from_user()
                if ssid is None:
                    log.info("WiFi magically came back before user input.")
                    break
                log.info("Will try to connect to SSID: {}".format(ssid))
                console.big_image('images/wifi_pending.png')
                console.big_status('Trying to connect...')
                did_connect = wireless.connect(ssid, password)
                has_internet = has_internet_access_multi_try() if did_connect else False
                if not did_connect or not has_internet:
                    if did_connect:
                        wireless.delete_connection(ssid)
                        msg = 'Connected to WiFi...\nbut no internet detected.\nPlease use another network.'
                    else:
                        msg = 'WiFi credentials did not work.\nDid you type them correctly?\nPlease try again.'
                    log.info(msg)
                    console.big_image('images/wifi_error.png')
                    console.big_status(msg)
                else:
                    log.info("Success! Connected to SSID: {}".format(ssid))
                    console.big_image('images/wifi_success.png')
                    console.big_status('WiFi connection success!')
                    time.sleep(5)
                    print_connection_info()
                    break
            console.big_clear()

            update_and_reboot_if_no_token()

    else:
        # We have WiFi.
        # After WiFi, we care that we have a Token so that we can authenticate with the CDP.
        ensure_token()

    time.sleep(5)

