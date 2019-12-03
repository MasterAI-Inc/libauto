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
The microcontroller acts as an I2C slave. Let's get a connection to it.
"""
CONTROLLER_I2C_SLAVE_ADDRESS = 0x14
from . import easyi2c
FD = easyi2c.open_i2c(1, CONTROLLER_I2C_SLAVE_ADDRESS)


"""
We'll go ahead and get the capabilities here, so that we have them ready to
go for whoever imports this module.
"""
from . import capabilities
CAPS = capabilities.get_capabilities(FD, soft_reset_first=True, detect_enabledness=True)


"""
We'll make it easy to enable and disable components as well.
"""
def acquire_component_interface(component_name):
    return capabilities.acquire_component_interface(FD, CAPS, component_name)

def dispose_component_interface(interface):
    return capabilities.dispose_component_interface(interface)


"""
Try our best to cleanup when this python process exits.
We clean up by telling the microcontroller to reset itself.
"""
from . import reset
import atexit, time, signal

def cleanup():
    time.sleep(0.1)
    reset.soft_reset(FD)

atexit.register(cleanup)

def handle_sig_hup(signum, frame):
    # By default, the Python process will not handle this signal.
    # Furthermore, Python cannot call the "atexit" routines whenever
    # the process exits due to an unhandled signal. Therefore, by
    # default, our "cleanup" function above would not be called
    # if this process were to receive this signal. This is bad for us
    # because our PTY manager sends this signal whenever the user
    # clicks the "STOP" button on the CDP. All is well and good if
    # we just handle this signal. So we are.
    raise KeyboardInterrupt("STOP button pressed")

signal.signal(signal.SIGHUP, handle_sig_hup)

