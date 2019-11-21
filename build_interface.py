import types
import inspect


def build_interface(iface, impl_transport):
    if 'typename' in iface:
        # This is an object with inner stuff.
        name = iface['name']
        typename = iface['typename']
        TheDynamicType = type(typename, (), {})
        instance = TheDynamicType()

        for iface in iface['ifaces']:
            sub_name, attr = build_interface(iface, impl_transport)
            setattr(instance, sub_name, attr)

        return name, instance

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
    def params_0():
        return impl_transport(path, [])

    def params_1(a_0):
        return impl_transport(path, [a_0])

    def params_2(a_0, a_1):
        return impl_transport(path, [a_0, a_1])

    def params_3(a_0, a_1, a_2):
        return impl_transport(path, [a_0, a_1, a_2])

    def params_4(a_0, a_1, a_2, a_3):
        return impl_transport(path, [a_0, a_1, a_2, a_3])

    def params_5(a_0, a_1, a_2, a_3, a_4):
        return impl_transport(path, [a_0, a_1, a_2, a_3, a_4])

    def params_6(a_0, a_1, a_2, a_3, a_4, a_5):
        return impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5])

    def params_7(a_0, a_1, a_2, a_3, a_4, a_5, a_6):
        return impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6])

    def params_8(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7):
        return impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7])

    def params_9(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8):
        return impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8])

    def params_10(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9):
        return impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9])

    def params_11(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10):
        return impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10])

    def params_12(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11):
        return impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11])

    def params_13(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12):
        return impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12])

    def params_14(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13):
        return impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13])

    def params_15(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14):
        return impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14])

    def params_16(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15):
        return impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15])

    def params_17(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16):
        return impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16])

    def params_18(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17):
        return impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17])

    def params_19(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18):
        return impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18])

    def params_20(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19):
        return impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19])

    def params_21(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20):
        return impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20])

    def params_22(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21):
        return impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21])

    def params_23(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22):
        return impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22])

    def params_24(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23):
        return impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23])

    def params_25(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24):
        return impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24])

    def params_26(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25):
        return impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25])

    def params_27(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26):
        return impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26])

    def params_28(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27):
        return impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27])

    def params_29(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28):
        return impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28])

    def params_30(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29):
        return impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29])

    def params_31(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30):
        return impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30])

    def params_32(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31):
        return impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31])

    def params_33(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32):
        return impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32])

    def params_34(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33):
        return impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33])

    def params_35(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33, a_34):
        return impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33, a_34])

    def params_36(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33, a_34, a_35):
        return impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33, a_34, a_35])

    def params_37(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33, a_34, a_35, a_36):
        return impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33, a_34, a_35, a_36])

    def params_38(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33, a_34, a_35, a_36, a_37):
        return impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33, a_34, a_35, a_36, a_37])

    def params_39(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33, a_34, a_35, a_36, a_37, a_38):
        return impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33, a_34, a_35, a_36, a_37, a_38])

    def params_40(a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33, a_34, a_35, a_36, a_37, a_38, a_39):
        return impl_transport(path, [a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8, a_9, a_10, a_11, a_12, a_13, a_14, a_15, a_16, a_17, a_18, a_19, a_20, a_21, a_22, a_23, a_24, a_25, a_26, a_27, a_28, a_29, a_30, a_31, a_32, a_33, a_34, a_35, a_36, a_37, a_38, a_39])

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

