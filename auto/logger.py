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
Provide a standardized logging format. Modules which would like to log should do
so with the following code (just an example):

    ```python
    from auto import logger
    log = logger.init(__name__, terminal=True)
    ...
    log.info("Stuff...")
    ```
"""

import logging


def set_root_log_level(level=logging.INFO):
    logging.getLogger().setLevel(level)


set_root_log_level()


def _get_formatter():
    formatter = logging.Formatter('%(asctime)s: %(name)-35s: %(levelname)-10s: %(message)s')
    return formatter


def init(modulename, terminal=True, filename=None, log_level=logging.NOTSET):
    """
    Build a logger to be used as a global at the module-level.
    """
    log = logging.getLogger(modulename)
    log.setLevel(log_level)

    if filename:
        handler = logging.FileHandler(filename)  # <-- log to that file
        handler.setLevel(log_level)
        handler.setFormatter(_get_formatter())
        log.addHandler(handler)

    if terminal:
        handler = logging.StreamHandler()   # <-- log to the terminal
        handler.setLevel(log_level)
        handler.setFormatter(_get_formatter())
        log.addHandler(handler)

    return log

