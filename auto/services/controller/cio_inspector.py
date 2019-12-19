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
This module provides helper functions for the RPC controller server and client.
"""

import inspect
import cio


def build_cio_class_map():
    abs_classes = inspect.getmembers(cio, predicate=inspect.isabstract)
    return {class_name: class_type for class_name, class_type in abs_classes}


def build_cio_method_map():
    m = {}

    abs_classes = build_cio_class_map()

    for class_name, class_type in abs_classes.items():
        methods = inspect.getmembers(class_type, predicate=inspect.isfunction)
        m[class_name] = [method_name for method_name, method_ref in methods]

    return m


def get_abc_superclass_name(obj):
    mro = inspect.getmro(type(obj))
    superclass = mro[1]
    assert inspect.isabstract(superclass)
    superclass_name = superclass.__name__
    return superclass_name

