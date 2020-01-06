###############################################################################
#
# Copyright (c) 2017-2018 AutoAuto, LLC
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from AutoAuto, LLC.
#
###############################################################################

"""
This modules defines the interface for interacting programmatically
between your device and you online account at AutoAuto Labs.
"""

import abc


class LabsServiceIface(abc.ABC):
    """
    This is the front-door interface for communicating with the AutoAuto Labs
    servers from your device. This interface allows you to programmatically
    interact with your account at AutoAuto Labs from the code running on your
    device.
    """

    @abc.abstractmethod
    async def connect(self):
        """
        Connect the backend service.
        """
        pass

    @abc.abstractmethod
    async def send(self, msg):
        """
        Send a message `msg` to your AutoAuto Labs account.
        Return True if the message was sent, else return False.
        """
        pass

    @abc.abstractmethod
    async def close(self):
        """
        Close the backend connection.
        """
        pass

