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
This module is used to dynamically build Python types, methods, and functions
which conform to an interface description. These types, methods, and functions
delegate the implementation to a remote server. The goal is that, using this
module, you can construct a Python interface that feels like the "real deal"
but is actually delegate over a wire in the background (doing RPC).
"""

import types


def build_interface(iface, impl_transport, is_method=False):
    """
    This is the entry-point function for building the Python interface from
    the given description (`iface`). All operations are delegated to the
    back-end server by invoking the `impl_transport` function.
    """
    if 'typename' in iface:
        # This is an object with inner stuff.
        typename = iface['typename']
        TheDynamicType = type(typename, (object,), {})
        instance = TheDynamicType()

        for i in iface['ifaces']:
            if ('ismethod' in i) and i['ismethod']:
                sub_name, attr = build_interface(i, impl_transport, is_method=True)
                setattr(TheDynamicType, sub_name, attr)
            else:
                sub_name, attr = build_interface(i, impl_transport, is_method=False)
                setattr(instance, sub_name, attr)

        TheDynamicType.__module__ = iface['module']
        TheDynamicType.__doc__ = iface['doc']

        return iface['name'], instance

    else:
        # This is just a single callable.
        name         = iface['name']
        args         = iface['args']
        default_args = iface['defaults']
        module       = iface['module']
        doc          = iface['doc']
        filename     = iface['filename']
        firstlineno  = iface['firstlineno']
        path         = iface['path']

        if is_method:
            args = ['self'] + list(args)
            template = _brute_force_method_params(path, impl_transport, len(args))

        else:
            template = _brute_force_function_params(path, impl_transport, len(args))

        code = _build_code(name, args, template.__code__, filename, firstlineno)
        func = _build_function(code, template, default_args)

        func.__module__ = module
        func.__doc__ = doc

        return name, func


def _build_code(name, args, template_code, filename, firstlineno):
    template_inner_var_names = template_code.co_varnames[template_code.co_argcount:]
    new_varnames = tuple(args) + template_inner_var_names

    code = types.CodeType(
        len(args),                               # argcount
        template_code.co_kwonlyargcount,         # kwonlyargcount
        template_code.co_nlocals,                # nlocals
        template_code.co_stacksize,              # stacksize
        template_code.co_flags,                  # flags
        template_code.co_code,                   # codestring
        template_code.co_consts,                 # constants
        template_code.co_names,                  # names
        new_varnames,                            # varnames
        filename,                                # filename
        name,                                    # name
        firstlineno,                             # firstlineno
        template_code.co_lnotab,                 # lnotab
        template_code.co_freevars,               # freevars
        template_code.co_cellvars,               # cellvars
    )

    return code


def _build_function(code, template_func, default_args):
    func = types.FunctionType(code, template_func.__globals__, code.co_name, default_args, template_func.__closure__)
    return func


def _brute_force_function_params(path, impl_transport, argcount):
    async def params_0():
        return await impl_transport(path, [])

    async def params_1(a_0):
        return await impl_transport(path, [a_0])

    async def params_2(a_0, a_1):
        return await impl_transport(path, [a_0, a_1])

    async def params_3(a_0, a_1, a_2):
        return await impl_transport(path, [a_0, a_1, a_2])

    async def params_4(a_0, a_1, a_2, a_3):
        return await impl_transport(path, [a_0, a_1, a_2, a_3])

    async def params_5(a_0, a_1, a_2, a_3, a_4):
        return await impl_transport(path, [a_0, a_1, a_2, a_3, a_4])

    async def params_6(a_0, a_1, a_2, a_3, a_4, a_5):
        return await impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5])

    async def params_7(a_0, a_1, a_2, a_3, a_4, a_5, a_6):
        return await impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6])

    async def params_8(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7):
        return await impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7])

    async def params_9(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8):
        return await impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8])

    async def params_10(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9):
        return await impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9])

    async def params_11(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10):
        return await impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10])

    async def params_12(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11):
        return await impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11])

    async def params_13(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12):
        return await impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12])

    async def params_14(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13):
        return await impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13])

    async def params_15(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14):
        return await impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14])

    async def params_16(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15):
        return await impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15])

    async def params_17(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16):
        return await impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16])

    async def params_18(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17):
        return await impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17])

    async def params_19(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18):
        return await impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18])

    async def params_20(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19):
        return await impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19])

    async def params_21(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20):
        return await impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20])

    async def params_22(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21):
        return await impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21])

    async def params_23(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22):
        return await impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22])

    async def params_24(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23):
        return await impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23])

    async def params_25(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24):
        return await impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24])

    async def params_26(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25):
        return await impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25])

    async def params_27(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26):
        return await impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26])

    async def params_28(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27):
        return await impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27])

    async def params_29(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28):
        return await impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28])

    async def params_30(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29):
        return await impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29])

    async def params_31(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30):
        return await impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30])

    async def params_32(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31):
        return await impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31])

    async def params_33(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32):
        return await impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32])

    async def params_34(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33):
        return await impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33])

    async def params_35(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33, a_34):
        return await impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33, a_34])

    async def params_36(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33, a_34, a_35):
        return await impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33, a_34, a_35])

    async def params_37(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33, a_34, a_35, a_36):
        return await impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33, a_34, a_35, a_36])

    async def params_38(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33, a_34, a_35, a_36, a_37):
        return await impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33, a_34, a_35, a_36, a_37])

    async def params_39(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33, a_34, a_35, a_36, a_37, a_38):
        return await impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33, a_34, a_35, a_36, a_37, a_38])

    async def params_40(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33, a_34, a_35, a_36, a_37, a_38, a_39):
        return await impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33, a_34, a_35, a_36, a_37, a_38, a_39])

    return {
        0: params_0,
        1: params_1,
        2: params_2,
        3: params_3,
        4: params_4,
        5: params_5,
        6: params_6,
        7: params_7,
        8: params_8,
        9: params_9,
        10: params_10,
        11: params_11,
        12: params_12,
        13: params_13,
        14: params_14,
        15: params_15,
        16: params_16,
        17: params_17,
        18: params_18,
        19: params_19,
        20: params_20,
        21: params_21,
        22: params_22,
        23: params_23,
        24: params_24,
        25: params_25,
        26: params_26,
        27: params_27,
        28: params_28,
        29: params_29,
        30: params_30,
        31: params_31,
        32: params_32,
        33: params_33,
        34: params_34,
        35: params_35,
        36: params_36,
        37: params_37,
        38: params_38,
        39: params_39,
        40: params_40,
    }[argcount]


def _brute_force_method_params(path, impl_transport, argcount):
    async def params_1(self):
        return await impl_transport(path, [])

    async def params_2(self, a_1):
        return await impl_transport(path, [a_1])

    async def params_3(self, a_1, a_2):
        return await impl_transport(path, [a_1, a_2])

    async def params_4(self, a_1, a_2, a_3):
        return await impl_transport(path, [a_1, a_2, a_3])

    async def params_5(self, a_1, a_2, a_3, a_4):
        return await impl_transport(path, [a_1, a_2, a_3, a_4])

    async def params_6(self, a_1, a_2, a_3, a_4, a_5):
        return await impl_transport(path, [a_1, a_2, a_3, a_4, a_5])

    async def params_7(self, a_1, a_2, a_3, a_4, a_5, a_6):
        return await impl_transport(path, [a_1, a_2, a_3, a_4, a_5, a_6])

    async def params_8(self, a_1, a_2, a_3, a_4, a_5, a_6, a_7):
        return await impl_transport(path, [a_1, a_2, a_3, a_4, a_5, a_6, a_7])

    async def params_9(self, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8):
        return await impl_transport(path, [a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8])

    async def params_10(self, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9):
        return await impl_transport(path, [a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9])

    async def params_11(self, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10):
        return await impl_transport(path, [a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10])

    async def params_12(self, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11):
        return await impl_transport(path, [a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11])

    async def params_13(self, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12):
        return await impl_transport(path, [a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12])

    async def params_14(self, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13):
        return await impl_transport(path, [a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13])

    async def params_15(self, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14):
        return await impl_transport(path, [a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14])

    async def params_16(self, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15):
        return await impl_transport(path, [a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15])

    async def params_17(self, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16):
        return await impl_transport(path, [a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16])

    async def params_18(self, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17):
        return await impl_transport(path, [a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17])

    async def params_19(self, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18):
        return await impl_transport(path, [a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18])

    async def params_20(self, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19):
        return await impl_transport(path, [a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19])

    async def params_21(self, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20):
        return await impl_transport(path, [a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20])

    async def params_22(self, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21):
        return await impl_transport(path, [a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21])

    async def params_23(self, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22):
        return await impl_transport(path, [a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22])

    async def params_24(self, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23):
        return await impl_transport(path, [a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23])

    async def params_25(self, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24):
        return await impl_transport(path, [a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24])

    async def params_26(self, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25):
        return await impl_transport(path, [a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25])

    async def params_27(self, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26):
        return await impl_transport(path, [a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26])

    async def params_28(self, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27):
        return await impl_transport(path, [a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27])

    async def params_29(self, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28):
        return await impl_transport(path, [a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28])

    async def params_30(self, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29):
        return await impl_transport(path, [a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29])

    async def params_31(self, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30):
        return await impl_transport(path, [a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30])

    async def params_32(self, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31):
        return await impl_transport(path, [a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31])

    async def params_33(self, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32):
        return await impl_transport(path, [a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32])

    async def params_34(self, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33):
        return await impl_transport(path, [a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33])

    async def params_35(self, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33, a_34):
        return await impl_transport(path, [a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33, a_34])

    async def params_36(self, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33, a_34, a_35):
        return await impl_transport(path, [a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33, a_34, a_35])

    async def params_37(self, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33, a_34, a_35, a_36):
        return await impl_transport(path, [a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33, a_34, a_35, a_36])

    async def params_38(self, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33, a_34, a_35, a_36, a_37):
        return await impl_transport(path, [a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33, a_34, a_35, a_36, a_37])

    async def params_39(self, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33, a_34, a_35, a_36, a_37, a_38):
        return await impl_transport(path, [a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33, a_34, a_35, a_36, a_37, a_38])

    async def params_40(self, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33, a_34, a_35, a_36, a_37, a_38, a_39):
        return await impl_transport(path, [a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33, a_34, a_35, a_36, a_37, a_38, a_39])

    return {
        1: params_1,
        2: params_2,
        3: params_3,
        4: params_4,
        5: params_5,
        6: params_6,
        7: params_7,
        8: params_8,
        9: params_9,
        10: params_10,
        11: params_11,
        12: params_12,
        13: params_13,
        14: params_14,
        15: params_15,
        16: params_16,
        17: params_17,
        18: params_18,
        19: params_19,
        20: params_20,
        21: params_21,
        22: params_22,
        23: params_23,
        24: params_24,
        25: params_25,
        26: params_26,
        27: params_27,
        28: params_28,
        29: params_29,
        30: params_30,
        31: params_31,
        32: params_32,
        33: params_33,
        34: params_34,
        35: params_35,
        36: params_36,
        37: params_37,
        38: params_38,
        39: params_39,
        40: params_40,
    }[argcount]

