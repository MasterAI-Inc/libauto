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
This RPC server exposes the standard CIO interface, allowing multiple
processes to share the CIO resources.
"""

from auto.rpc.server import serve, SerializeIface

import cio
from cio.known_impls import known_impls

import os
import uuid
import asyncio
import inspect
import importlib

from auto import logger
log = logger.init('controller_rpc_server', terminal=True)

from cio_inspector import build_cio_method_map, get_abc_superclass_name


async def _get_cio_implementation():
    fixed_impl = os.environ.get('CIO_IMPLEMENTATION', None)

    if fixed_impl is not None:
        list_of_impls = [fixed_impl]
        log.info('Environment specifies cio implementation: {}'.format(fixed_impl))
    else:
        list_of_impls = known_impls
        log.info('Environment does not specify cio implementation, using known list: {}'.format(known_impls))

    for impl in list_of_impls:
        impl_module = importlib.import_module(impl)

        impl_classes = inspect.getmembers(impl_module, predicate=inspect.isclass)

        cio_root_class_types = []

        for class_name, class_type in impl_classes:
            superclass_type = inspect.getmro(class_type)[1]  # first superclass
            if superclass_type is cio.CioRoot:
                cio_root_class_types.append(class_type)

        if len(cio_root_class_types) == 0:
            log.error('Failed to find cio.CioRoot implementation in module: {}'.format(impl))
            continue

        if len(cio_root_class_types) > 1:
            log.warn('There are more than one cio.CioRoot implementation in module: {}'.format(impl))

        for cio_root_class_type in cio_root_class_types:
            cio_root = cio_root_class_type()

            try:
                log.info('Will attempt to initialize cio implementation: {} from module: {}'.format(type(cio_root), impl))
                caps = await cio_root.init()
                log.info('Successfully initialized cio implementation: {} from module: {}'.format(type(cio_root), impl))
                return cio_root, caps

            except Exception as e:
                log.info('Failed to initialize cio implementation: {} from module: {}; error: {}'.format(type(cio_root), impl, e))

    return None, None


def _wrap_value_in_async_func(val):
    async def get():
        return val
    return get


async def init(loop):
    cio_root, caps = await _get_cio_implementation()

    if caps is None:
        log.error('Failed to find cio implementation, quitting...')
        return

    cio_map = build_cio_method_map()

    class CioIface:
        async def setup(self, ws):
            self.ws = ws
            self.acquired = {}
            log.info('CLIENT CONNECTED: {}'.format(self.ws.remote_address))

        async def export_init(self):
            return caps

        async def export_acquire(self, capability_id):
            capability_obj = await cio_root.acquire(capability_id)
            rpc_guid = str(uuid.uuid4())
            self.acquired[rpc_guid] = capability_obj
            capability_obj.export_get_rpc_guid = _wrap_value_in_async_func(rpc_guid)
            superclass_name = get_abc_superclass_name(capability_obj)
            cap_methods = cio_map[superclass_name]
            raise SerializeIface(capability_obj, whitelist_method_names=cap_methods)

        async def export_release(self, rpc_guid):
            if rpc_guid in self.acquired:
                capability_obj = self.acquired[rpc_guid]
                del self.acquired[rpc_guid]
                await cio_root.release(capability_obj)

        async def cleanup(self):
            for rpc_guid in list(self.acquired):  # copy keys
                await self.export_release(rpc_guid)
            log.info('CLIENT DISCONNECTED: {}'.format(self.ws.remote_address))

    pubsub_iface = None

    server = await serve(CioIface, pubsub_iface, 'localhost', 7002)

    log.info("RUNNING!")

    return server


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    server = loop.run_until_complete(init(loop))
    if server is not None:
        loop.run_forever()

