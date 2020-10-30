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
This RPC server provides the standard CUI interface, allowing multiple
processes to share the CUI resources.
"""

from auto.rpc.server import serve

import cui
from cui.known_impls import known_impls

import os
import asyncio
import inspect
import importlib

from auto import logger
log = logger.init(__name__, terminal=True)


async def _safe_invoke(func, *args):
    if asyncio.iscoroutinefunction(func):
        return await func(*args)
    else:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, func, *args)


async def _get_cui_implementation():
    fixed_impl = os.environ.get('CUI_IMPLEMENTATION', None)

    if fixed_impl is not None:
        list_of_impls = [fixed_impl]
        log.info('Environment specifies cui implementation: {}'.format(fixed_impl))
    else:
        list_of_impls = known_impls
        log.info('Environment does not specify cui implementation, using known list: {}'.format(known_impls))

    for impl in list_of_impls:
        impl_module = importlib.import_module(impl)

        impl_classes = inspect.getmembers(impl_module, predicate=inspect.isclass)

        cui_root_class_types = []

        for class_name, class_type in impl_classes:
            superclass_type = inspect.getmro(class_type)[1]  # first superclass
            if superclass_type is cui.CuiRoot:
                cui_root_class_types.append(class_type)

        if len(cui_root_class_types) == 0:
            log.error('Failed to find cui.CuiRoot implementation in module: {}'.format(impl))
            continue

        if len(cui_root_class_types) > 1:
            log.warn('There are more than one cui.CuiRoot implementation in module: {}'.format(impl))

        for cui_root_class_type in cui_root_class_types:
            cui_root = cui_root_class_type()

            try:
                log.info('Will attempt to initialize cui implementation: {} from module: {}'.format(type(cui_root), impl))
                result = await _safe_invoke(cui_root.init)
                log.info('Successfully initialized cui implementation: {} from module: {}'.format(type(cui_root), impl))
                return cui_root, result

            except Exception as e:
                log.info('Failed to initialize cui implementation: {} from module: {}; error: {}'.format(type(cui_root), impl, e))

    return None, None


async def init():
    cui_root, _ = await _get_cui_implementation()

    if cui_root is None:
        log.error('Failed to find cui implementation, quitting...')
        return

    whitelist_method_names = tuple([method_name for method_name, method_ref in inspect.getmembers(cui.CuiRoot, predicate=inspect.isfunction)])

    def root_factory():
        return cui_root, whitelist_method_names

    pubsub_iface = None

    server = await serve(root_factory, pubsub_iface, '127.0.0.1', 7003)

    log.info("RUNNING!")

    return server


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    server = loop.run_until_complete(init())
    if server is not None:
        loop.run_forever()

