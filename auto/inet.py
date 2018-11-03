"""
This file is a modified version of joshvillbrandt's wireless library which
is distributed on GitHub (link below) under the Apache License (a copy of
the original license is below).

https://github.com/joshvillbrandt/wireless

Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   1. Definitions.

      "License" shall mean the terms and conditions for use, reproduction,
      and distribution as defined by Sections 1 through 9 of this document.

      "Licensor" shall mean the copyright owner or entity authorized by
      the copyright owner that is granting the License.

      "Legal Entity" shall mean the union of the acting entity and all
      other entities that control, are controlled by, or are under common
      control with that entity. For the purposes of this definition,
      "control" means (i) the power, direct or indirect, to cause the
      direction or management of such entity, whether by contract or
      otherwise, or (ii) ownership of fifty percent (50%) or more of the
      outstanding shares, or (iii) beneficial ownership of such entity.

      "You" (or "Your") shall mean an individual or Legal Entity
      exercising permissions granted by this License.

      "Source" form shall mean the preferred form for making modifications,
      including but not limited to software source code, documentation
      source, and configuration files.

      "Object" form shall mean any form resulting from mechanical
      transformation or translation of a Source form, including but
      not limited to compiled object code, generated documentation,
      and conversions to other media types.

      "Work" shall mean the work of authorship, whether in Source or
      Object form, made available under the License, as indicated by a
      copyright notice that is included in or attached to the work
      (an example is provided in the Appendix below).

      "Derivative Works" shall mean any work, whether in Source or Object
      form, that is based on (or derived from) the Work and for which the
      editorial revisions, annotations, elaborations, or other modifications
      represent, as a whole, an original work of authorship. For the purposes
      of this License, Derivative Works shall not include works that remain
      separable from, or merely link (or bind by name) to the interfaces of,
      the Work and Derivative Works thereof.

      "Contribution" shall mean any work of authorship, including
      the original version of the Work and any modifications or additions
      to that Work or Derivative Works thereof, that is intentionally
      submitted to Licensor for inclusion in the Work by the copyright owner
      or by an individual or Legal Entity authorized to submit on behalf of
      the copyright owner. For the purposes of this definition, "submitted"
      means any form of electronic, verbal, or written communication sent
      to the Licensor or its representatives, including but not limited to
      communication on electronic mailing lists, source code control systems,
      and issue tracking systems that are managed by, or on behalf of, the
      Licensor for the purpose of discussing and improving the Work, but
      excluding communication that is conspicuously marked or otherwise
      designated in writing by the copyright owner as "Not a Contribution."

      "Contributor" shall mean Licensor and any individual or Legal Entity
      on behalf of whom a Contribution has been received by Licensor and
      subsequently incorporated within the Work.

   2. Grant of Copyright License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      copyright license to reproduce, prepare Derivative Works of,
      publicly display, publicly perform, sublicense, and distribute the
      Work and such Derivative Works in Source or Object form.

   3. Grant of Patent License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      (except as stated in this section) patent license to make, have made,
      use, offer to sell, sell, import, and otherwise transfer the Work,
      where such license applies only to those patent claims licensable
      by such Contributor that are necessarily infringed by their
      Contribution(s) alone or by combination of their Contribution(s)
      with the Work to which such Contribution(s) was submitted. If You
      institute patent litigation against any entity (including a
      cross-claim or counterclaim in a lawsuit) alleging that the Work
      or a Contribution incorporated within the Work constitutes direct
      or contributory patent infringement, then any patent licenses
      granted to You under this License for that Work shall terminate
      as of the date such litigation is filed.

   4. Redistribution. You may reproduce and distribute copies of the
      Work or Derivative Works thereof in any medium, with or without
      modifications, and in Source or Object form, provided that You
      meet the following conditions:

      (a) You must give any other recipients of the Work or
          Derivative Works a copy of this License; and

      (b) You must cause any modified files to carry prominent notices
          stating that You changed the files; and

      (c) You must retain, in the Source form of any Derivative Works
          that You distribute, all copyright, patent, trademark, and
          attribution notices from the Source form of the Work,
          excluding those notices that do not pertain to any part of
          the Derivative Works; and

      (d) If the Work includes a "NOTICE" text file as part of its
          distribution, then any Derivative Works that You distribute must
          include a readable copy of the attribution notices contained
          within such NOTICE file, excluding those notices that do not
          pertain to any part of the Derivative Works, in at least one
          of the following places: within a NOTICE text file distributed
          as part of the Derivative Works; within the Source form or
          documentation, if provided along with the Derivative Works; or,
          within a display generated by the Derivative Works, if and
          wherever such third-party notices normally appear. The contents
          of the NOTICE file are for informational purposes only and
          do not modify the License. You may add Your own attribution
          notices within Derivative Works that You distribute, alongside
          or as an addendum to the NOTICE text from the Work, provided
          that such additional attribution notices cannot be construed
          as modifying the License.

      You may add Your own copyright statement to Your modifications and
      may provide additional or different license terms and conditions
      for use, reproduction, or distribution of Your modifications, or
      for any such Derivative Works as a whole, provided Your use,
      reproduction, and distribution of the Work otherwise complies with
      the conditions stated in this License.

   5. Submission of Contributions. Unless You explicitly state otherwise,
      any Contribution intentionally submitted for inclusion in the Work
      by You to the Licensor shall be under the terms and conditions of
      this License, without any additional terms or conditions.
      Notwithstanding the above, nothing herein shall supersede or modify
      the terms of any separate license agreement you may have executed
      with Licensor regarding such Contributions.

   6. Trademarks. This License does not grant permission to use the trade
      names, trademarks, service marks, or product names of the Licensor,
      except as required for reasonable and customary use in describing the
      origin of the Work and reproducing the content of the NOTICE file.

   7. Disclaimer of Warranty. Unless required by applicable law or
      agreed to in writing, Licensor provides the Work (and each
      Contributor provides its Contributions) on an "AS IS" BASIS,
      WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
      implied, including, without limitation, any warranties or conditions
      of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A
      PARTICULAR PURPOSE. You are solely responsible for determining the
      appropriateness of using or redistributing the Work and assume any
      risks associated with Your exercise of permissions under this License.

   8. Limitation of Liability. In no event and under no legal theory,
      whether in tort (including negligence), contract, or otherwise,
      unless required by applicable law (such as deliberate and grossly
      negligent acts) or agreed to in writing, shall any Contributor be
      liable to You for damages, including any direct, indirect, special,
      incidental, or consequential damages of any character arising as a
      result of this License or out of the use or inability to use the
      Work (including but not limited to damages for loss of goodwill,
      work stoppage, computer failure or malfunction, or any and all
      other commercial damages or losses), even if such Contributor
      has been advised of the possibility of such damages.

   9. Accepting Warranty or Additional Liability. While redistributing
      the Work or Derivative Works thereof, You may choose to offer,
      and charge a fee for, acceptance of support, warranty, indemnity,
      or other liability obligations and/or rights consistent with this
      License. However, in accepting such obligations, You may act only
      on Your own behalf and on Your sole responsibility, not on behalf
      of any other Contributor, and only if You agree to indemnify,
      defend, and hold each Contributor harmless for any liability
      incurred by, or claims asserted against, such Contributor by reason
      of your accepting any such warranty or additional liability.

   END OF TERMS AND CONDITIONS

   APPENDIX: How to apply the Apache License to your work.

      To apply the Apache License to your work, attach the following
      boilerplate notice, with the fields enclosed by brackets "{}"
      replaced with your own identifying information. (Don't include
      the brackets!)  The text should be enclosed in the appropriate
      comment syntax for the file format. We also recommend that a
      file or class name and description of purpose be included on the
      same "printed page" as the copyright notice for easier
      identification within third-party archives.

   Copyright {yyyy} {name of copyright owner}

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

from abc import ABCMeta, abstractmethod
import subprocess
from time import sleep
from packaging import version

import socket
import fcntl
import struct


# send a command to the shell and return the result
def cmd(cmd):
    output = subprocess.run(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT).stdout.decode('utf-8')
    return output


# abstracts away wireless connection
class Wireless:
    _driver_name = None
    _driver = None

    # init
    def __init__(self, interface=None):
        # detect and init appropriate driver
        self._driver_name = self._detectDriver()
        if self._driver_name == 'nmcli':
            self._driver = NmcliWireless(interface=interface)
        elif self._driver_name == 'nmcli0990':
            self._driver = Nmcli0990Wireless(interface=interface)
        elif self._driver_name == 'wpa_supplicant':
            self._driver = WpasupplicantWireless(interface=interface)
        elif self._driver_name == 'networksetup':
            self._driver = NetworksetupWireless(interface=interface)

        # attempt to auto detect the interface if none was provided
        if self.interface() is None:
            interfaces = self.interfaces()
            if len(interfaces) > 0:
                self.interface(interfaces[0])

        # raise an error if there is still no interface defined
        if self.interface() is None:
            raise Exception('Unable to auto-detect the network interface.')

    def _detectDriver(self):
        # try nmcli (Ubuntu 14.04)
        response = cmd('which nmcli'.split(' '))
        if len(response) > 0 and 'not found' not in response:
            response = cmd('nmcli --version'.split(' '))
            parts = response.split()
            ver = parts[-1]
            if version.parse(ver) > version.parse('0.9.9.0'):
                return 'nmcli0990'
            else:
                return 'nmcli'

        # try nmcli (Ubuntu w/o network-manager)
        response = cmd('which wpa_supplicant'.split(' '))
        if len(response) > 0 and 'not found' not in response:
            return 'wpa_supplicant'

        # try networksetup (Mac OS 10.10)
        response = cmd('which networksetup'.split(' '))
        if len(response) > 0 and 'not found' not in response:
            return 'networksetup'

        raise Exception('Unable to find compatible wireless driver.')

    # connect to a network
    def connect(self, ssid, password):
        return self._driver.connect(ssid, password)

    # return the ssid of the current network
    def current(self):
        return self._driver.current()

    # return a list of wireless adapters
    def interfaces(self):
        return self._driver.interfaces()

    # return the current wireless adapter
    def interface(self, interface=None):
        return self._driver.interface(interface)

    # return the current wireless adapter
    def power(self, power=None):
        return self._driver.power(power)

    # return the driver name
    def driver(self):
        return self._driver_name


# abstract class for all wireless drivers
class WirelessDriver:
    __metaclass__ = ABCMeta

    @abstractmethod
    def connect(self, ssid, password):
        pass

    @abstractmethod
    def current(self):
        pass

    @abstractmethod
    def interfaces(self):
        pass

    @abstractmethod
    def interface(self, interface=None):
        pass

    @abstractmethod
    def power(self, power=None):
        pass


# Linux nmcli Driver < 0.9.9.0
class NmcliWireless(WirelessDriver):
    _interface = None

    # init
    def __init__(self, interface=None):
        self.interface(interface)

    # clean up connections where partial is part of the connection name
    # this is needed to prevent the following error after extended use:
    # 'maximum number of pending replies per connection has been reached'
    def _clean(self, partial):
        # list matching connections
        response = cmd("nmcli --fields UUID,NAME con list".split(' '))

        # delete all of the matching connections
        for line in response.splitlines():
            if partial is None or partial not in line:
                continue
            if len(line) > 0:
                uuid = line.split()[0]
                cmd("nmcli con delete uuid".split(' ') + [uuid])

    # ignore warnings in nmcli output
    # sometimes there are warnings but we connected just fine
    def _errorInResponse(self, response):
        # no error if no response
        if len(response) == 0:
            return False

        # loop through each line
        for line in response.splitlines():
            # all error lines start with 'Error'
            if line.startswith('Error'):
                return True

        # if we didn't find an error then we are in the clear
        return False

    # connect to a network
    def connect(self, ssid, password):
        # clean up previous connection
        self._clean(self.current())

        # attempt to connect
        response = cmd("nmcli dev wifi connect".split(' ') +
                       [ssid, 'password', password, 'iface', self._interface])

        # parse response
        return not self._errorInResponse(response)

    # returned the ssid of the current network
    def current(self):
        iface = self.interface()
        # list active connections for all interfaces
        response = cmd("nmcli con status".split(' '))

        # the current network is in the first column
        for line in response.splitlines():
            if iface not in line:
                continue
            if len(line) > 0:
                return line.split()[0]

        # return none if there was not an active connection
        return None

    # return a list of wireless adapters
    def interfaces(self):
        # grab list of interfaces
        response = cmd('nmcli dev'.split(' '))

        # parse response
        interfaces = []
        for line in response.splitlines():
            if 'wireless' in line:
                # this line has our interface name in the first column
                interfaces.append(line.split()[0])

        # return list
        return interfaces

    # return the current wireless adapter
    def interface(self, interface=None):
        if interface is not None:
            self._interface = interface
        else:
            return self._interface

    # enable/disable wireless networking
    def power(self, power=None):
        if power is True:
            cmd('nmcli nm wifi on'.split(' '))
        elif power is False:
            cmd('nmcli nm wifi off'.split(' '))
        else:
            response = cmd('nmcli nm wifi'.split(' '))
            return 'enabled' in response


# Linux nmcli Driver >= 0.9.9.0
class Nmcli0990Wireless(WirelessDriver):
    _interface = None

    # init
    def __init__(self, interface=None):
        self.interface(interface)

    # clean up connections where partial is part of the connection name
    # this is needed to prevent the following error after extended use:
    # 'maximum number of pending replies per connection has been reached'
    def _clean(self, partial):
        # list matching connections
        response = cmd("nmcli --fields UUID,NAME con show".split(' '))

        # delete all of the matching connections
        for line in response.splitlines():
            if partial is None or partial not in line:
                continue
            if len(line) > 0:
                uuid = line.split()[0]
                cmd("nmcli con delete uuid".split(' ') + [uuid])

    # ignore warnings in nmcli output
    # sometimes there are warnings but we connected just fine
    def _errorInResponse(self, response):
        # no error if no response
        if len(response) == 0:
            return False

        # loop through each line
        for line in response.splitlines():
            # all error lines start with 'Error'
            if line.startswith('Error'):
                return True

        # if we didn't find an error then we are in the clear
        return False

    # connect to a network
    def connect(self, ssid, password):
        # clean up previous connection
        self._clean(self.current())

        # attempt to connect
        response = cmd("nmcli dev wifi connect".split(' ') +
                       [ssid, 'password', password, 'iface', self._interface])

        # parse response
        return not self._errorInResponse(response)

    # returned the ssid of the current network
    def current(self):
        iface = self.interface()
        # list active connections for all interfaces
        response = cmd("nmcli con".split(' '))

        # the current network is in the first column
        for line in response.splitlines():
            if iface not in line:
                continue
            if len(line) > 0:
                return line.split()[0]

        # return none if there was not an active connection
        return None

    # return a list of wireless adapters
    def interfaces(self):
        # grab list of interfaces
        response = cmd('nmcli dev'.split(' '))

        # parse response
        interfaces = []
        for line in response.splitlines():
            if 'wifi' in line:
                # this line has our interface name in the first column
                interfaces.append(line.split()[0])

        # return list
        return interfaces

    # return the current wireless adapter
    def interface(self, interface=None):
        if interface is not None:
            self._interface = interface
        else:
            return self._interface

    # enable/disable wireless networking
    def power(self, power=None):
        if power is True:
            cmd('nmcli r wifi on'.split(' '))
        elif power is False:
            cmd('nmcli r wifi off'.split(' '))
        else:
            response = cmd('nmcli r wifi'.split(' '))
            return 'enabled' in response


# Linux wpa_supplicant Driver
class WpasupplicantWireless(WirelessDriver):
    _file = '/tmp/wpa_supplicant.conf'
    _interface = None

    # init
    def __init__(self, interface=None):
        self.interface(interface)

    # connect to a network
    def connect(self, ssid, password):
        # attempt to stop any active wpa_supplicant instances
        # ideally we do this just for the interface we care about
        cmd('killall wpa_supplicant'.split(' '))

        # don't do DHCP for GoPros; can cause dropouts with the server
        cmd(["ifconfig", self._interface] + "10.5.5.10/24 up".split(' '))

        # create configuration file
        f = open(self._file, 'w')
        f.write('network={{\n    ssid="{}"\n    psk="{}"\n}}\n'.format(
            ssid, password))
        f.close()

        # attempt to connect
        cmd(["wpa_supplicant", "-i", self._interface, "-c", self._file, "-B"])

        # check that the connection was successful
        # i've never seen it take more than 3 seconds for the link to establish
        sleep(5)
        if self.current() != ssid:
            return False

        # attempt to grab an IP
        # better hope we are connected because the timeout here is really long
        # cmd(["dhclient", self._interface])

        # parse response
        return True

    # returned the ssid of the current network
    def current(self):
        # get interface status
        response = cmd(["iwconfig", self.interface()])

        # the current network is on the first line.
        # ex: wlan0     IEEE 802.11AC  ESSID:"SSID"  Nickname:"<WIFI@REALTEK>"
        line = response.splitlines()[0]
        match = re.search('ESSID:\"(.+?)\"', line)
        if match is not None:
            network = match.group(1)
            if network != 'off/any':
                return network

        # return none if there was not an active connection
        return None

    # return a list of wireless adapters
    def interfaces(self):
        # grab list of interfaces
        response = cmd(['iwconfig'])

        # parse response
        interfaces = []
        for line in response.splitlines():
            if len(line) > 0 and not line.startswith(' '):
                # this line contains an interface name!
                if 'no wireless extensions' not in line:
                    # this is a wireless interface
                    interfaces.append(line.split()[0])

        # return list
        return interfaces

    # return the current wireless adapter
    def interface(self, interface=None):
        if interface is not None:
            self._interface = interface
        else:
            return self._interface

    # enable/disable wireless networking
    def power(self, power=None):
        # not supported yet
        return None


# OS X networksetup Driver
class NetworksetupWireless(WirelessDriver):
    _interface = None

    # init
    def __init__(self, interface=None):
        self.interface(interface)

    # connect to a network
    def connect(self, ssid, password):
        # attempt to connect
        response = cmd(["networksetup", "-setairportnetwork", self._interface, ssid, password])

        # parse response - assume success when there is no response
        return (len(response) == 0)

    # returned the ssid of the current network
    def current(self):
        # attempt to get current network
        response = cmd(["networksetup", "-getairportnetwork", self._interface])

        # parse response
        phrase = 'Current Wi-Fi Network: '
        if phrase in response:
            return response.replace('Current Wi-Fi Network: ', '').strip()
        else:
            return None

    # return a list of wireless adapters
    def interfaces(self):
        # grab list of interfaces
        response = cmd('networksetup -listallhardwareports'.split(' '))

        # parse response
        interfaces = []
        detectedWifi = False
        for line in response.splitlines():
            if detectedWifi:
                # this line has our interface name in it
                interfaces.append(line.replace('Device: ', ''))
                detectedWifi = False
            else:
                # search for the line that has 'Wi-Fi' in it
                if 'Wi-Fi' in line:
                    detectedWifi = True

        # return list
        return interfaces

    # return the current wireless adapter
    def interface(self, interface=None):
        if interface is not None:
            self._interface = interface
        else:
            return self._interface

    # enable/disable wireless networking
    def power(self, power=None):
        if power is True:
            cmd(["networksetup", "-setairportpower", self._interface, "on"])
        elif power is False:
            cmd(["networksetup", "-setairportpower", self._interface, "off"])
        else:
            response = cmd(["networksetup", "-getairportpower", self._interface])
            return 'On' in response


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


if __name__ == '__main__':

    for iface in ['eth0', 'wlan0']:
        print(iface, get_ip_address(iface))

    wireless = Wireless('wlan0')
    print('WiFi interface', wireless.interface())
    print('WiFi SSID', wireless.current())

