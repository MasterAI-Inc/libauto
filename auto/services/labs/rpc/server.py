###############################################################################
#
# Copyright (c) 2017-2020 Master AI, Inc.
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from Master AI, Inc.
#
###############################################################################

from auto.rpc.server import serve

from auto import logger
log = logger.init(__name__, terminal=True)


class LabsService:
    def __init__(self):
        self.send_func = None

    async def export_send(self, msg):
        short_msg = ('string like ' + msg[:10] + '...') if isinstance(msg, str) else ('dict with keys: ' + repr(list(msg.keys())))
        if self.send_func is not None:
            log.info('Will send message to Labs; message: {}'.format(short_msg))
            return await self.send_func(msg)
        else:
            log.warning('Cannot send message to Labs; currently disconnected; message: {}'.format(short_msg))
            return False


async def init():
    interface = LabsService()

    interface_factory = lambda: interface    # we want to always return the same instance

    server, _ = await serve(interface_factory, None, 'localhost', 7004)

    return server, interface

