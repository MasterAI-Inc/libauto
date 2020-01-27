###############################################################################
#
# Copyright (c) 2017-2020 Master AI, Inc.
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from Master AI, Inc.
#
###############################################################################

"""
This module provides utilities for querying and controlling the network
interfaces of your device.

This is a **synchronous** interface.
"""

import subprocess
import socket
import fcntl
import struct
import time
import requests
import re


class Wireless:
    """
    Simple python interface to the `nmcli` utility.
    See: https://developer.gnome.org/NetworkManager/stable/nmcli.html
    """
    def __init__(self, interface=None):
        self.interface = interface

    def _error_in_response(self, response):
        for line in response.splitlines():
            if line.startswith('Error'):
                return True
        return False

    def connect(self, ssid, password):
        self.delete_connection(ssid)

        response = _run_cmd("nmcli dev wifi connect".split(' ') +
                            [ssid, 'password', password, 'ifname', self.interface,
                             'name', ssid])   # , 'hidden', 'yes'

        did_connect = not self._error_in_response(response)

        if not did_connect:
            self.delete_connection(ssid)

        time.sleep(2)    # Allow connection (and DHCP) to settle.

        _ = _run_cmd(["sync"])

        return did_connect

    def current(self):
        response = _run_cmd("nmcli --terse --field DEVICE,CONNECTION dev".split(' '))

        for line in response.splitlines():
            lst = line.split(':')
            if len(lst) != 2:
                continue
            iface, name = lst
            if iface == self.interface:
                if name in ('', '--'):
                    return None
                return name

        return None

    def delete_connection(self, ssid_to_delete):
        response = _run_cmd("nmcli --terse --fields UUID,NAME,TYPE con show".split(' '))

        for line in response.splitlines():
            lst = line.split(':')
            if len(lst) != 3:
                continue
            uuid, name, type_ = lst
            if type_ == '802-11-wireless' and ssid_to_delete in name:
                _run_cmd("nmcli con delete uuid".split(' ') + [uuid])

    def radio_power(self, on=None):
        if on is True:
            _run_cmd('nmcli radio wifi on'.split(' '))
        elif on is False:
            _run_cmd('nmcli radio wifi off'.split(' '))
        else:
            response = _run_cmd('nmcli radio wifi'.split(' '))
            return 'enabled' in response


def get_ip_address(ifname):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ret = socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', ifname[:15].encode('utf-8'))
        )[20:24])
        s.close()
        return ret
    except:
        # Humm...
        return None


def get_mac_address(ifname):
    output = _run_cmd(['ip', 'link', 'show', 'dev', ifname])
    match = re.search(r'ether ([^ ]+)', output)
    if match is not None:
        return match.group(1)


def has_internet_access():
    try:
        # Consider instead: https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.getaddrinfo
        params = socket.getaddrinfo('ws.autoauto.ai', 'https', proto=socket.IPPROTO_TCP)[0]
    except:
        return False
    family, type_, proto = params[:3]
    sockaddr = params[4]
    sock = socket.socket(family, type_, proto)
    sock.settimeout(20.0)
    try:
        sock.connect(sockaddr)   # <-- blocking, but respects the `settimeout()` call above
    except (socket.timeout, OSError):
        sock.close()
        return False
    sock.close()
    try:
        req = requests.get('http://api.autoauto.ai/ping', timeout=80.0)
        data = req.json()
        return req.status_code == 200 and data['text'] == 'pong'
    except:
        return False


def list_ifaces():
    response = _run_cmd('nmcli --terse --fields DEVICE,TYPE dev'.split(' '))

    interfaces = []
    for line in response.splitlines():
        lst = line.split(':')
        if len(lst) != 2:
            continue
        iface, type_ = lst
        interfaces.append(iface)

    return interfaces


def list_wifi_ifaces():
    response = _run_cmd('nmcli --terse --fields DEVICE,TYPE dev'.split(' '))

    interfaces = []
    for line in response.splitlines():
        lst = line.split(':')
        if len(lst) != 2:
            continue
        iface, type_ = lst
        if type_ == 'wifi':
            interfaces.append(iface)

    return interfaces


def _run_cmd(cmd):
    output = subprocess.run(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT).stdout.decode('utf-8')
    return output


if __name__ == '__main__':

    all_ifaces = list_ifaces()
    wifi_ifaces = list_wifi_ifaces()

    for iface in all_ifaces:
        print(iface, get_ip_address(iface))

    wireless = Wireless(wifi_ifaces[0])
    print('WiFi interface', wireless.interface)
    print('WiFi SSID', wireless.current())

