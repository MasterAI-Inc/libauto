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
        if self.send_func is not None:
            return await self.send_func(msg)
        else:
            return False


async def init(pubsub_channels):
    interface = LabsService()

    interface_factory = lambda: interface    # we want to always return the same instance

    pubsub = {
        'channels': pubsub_channels,
        'subscribe': None,
        'unsubscribe': None,
    }

    server, publish_func = await serve(interface_factory, pubsub, '127.0.0.1', 7004)

    return server, interface, publish_func

