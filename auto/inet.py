###############################################################################
#
# Copyright (c) 2017-2018 AutoAuto, LLC
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from AutoAuto, LLC.
#
###############################################################################

import subprocess

import socket
import fcntl
import struct


class Wireless:
    """
    Simple python interface to the `nmcli` utility.
    See: https://developer.gnome.org/NetworkManager/stable/nmcli.html
    """
    interface = None

    def __init__(self, interface=None):
        self.interface = interface

    def _delete_connection(self, ssid_to_delete):
        response = _run_cmd("nmcli --terse --fields UUID,NAME,TYPE con show".split(' '))

        for line in response.splitlines():
            uuid, name, type_ = line.split(':')
            if type_ == '802-11-wireless' and ssid_to_delete in name:
                _run_cmd("nmcli con delete uuid".split(' ') + [uuid])

    def _error_in_response(self, response):
        for line in response.splitlines():
            if line.startswith('Error'):
                return True
        return False

    def connect(self, ssid, password):
        self._delete_connection(ssid)

        response = _run_cmd("nmcli dev wifi connect".split(' ') +
                            [ssid, 'password', password, 'ifname', self.interface,
                             'name', ssid, 'hidden', 'yes'])

        did_connect = not self._error_in_response(response)

        if not did_connect:
            self._delete_connection(ssid)

        return did_connect

    def forget_current(self):
        name = self.current()
        self._delete_connection(name)

    def current(self):
        response = _run_cmd("nmcli --terse --field DEVICE,CONNECTION dev".split(' '))

        for line in response.splitlines():
            iface, name = line.split(':')
            if iface == self.interface:
                return name

        return None

    def radio_power(self, on=None):
        if power is True:
            _run_cmd('nmcli radio wifi on'.split(' '))
        elif power is False:
            _run_cmd('nmcli radio wifi off'.split(' '))
        else:
            response = _run_cmd('nmcli radio wifi'.split(' '))
            return 'enabled' in response


def get_ip_address(ifname):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', ifname[:15].encode('utf-8'))
        )[20:24])
    except:
        return None


def list_ifaces():
    response = _run_cmd('nmcli --terse --fields DEVICE,TYPE dev'.split(' '))

    interfaces = []
    for line in response.splitlines():
        iface, type_ = line.split(':')
        interfaces.append(iface)

    return interfaces


def list_wifi_ifaces():
    response = _run_cmd('nmcli --terse --fields DEVICE,TYPE dev'.split(' '))

    interfaces = []
    for line in response.splitlines():
        iface, type_ = line.split(':')
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

