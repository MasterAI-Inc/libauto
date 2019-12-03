"""
This package contains the interface to the microcontroller which we communicate
with via I2C from this host.

It's name is CIO (Controller Input/Output).
"""

import abc


#'Accelerometer': {'is_enabled': False, 'register_number': 13},
#'Calibrator': {'is_enabled': False, 'register_number': 16},
#'CarMotors': {'is_enabled': False, 'register_number': 11},
#'Encoders': {'is_enabled': False, 'register_number': 7},
#'Gyroscope': {'is_enabled': False, 'register_number': 14},
#'Gyroscope_accum': {'is_enabled': False, 'register_number': 15},
#'LEDs': {'is_enabled': False, 'register_number': 5},
#'LoopFrequency': {'is_enabled': False, 'register_number': 10},
#'PID_steering': {'is_enabled': False, 'register_number': 12},
#'Photoresistor': {'is_enabled': False, 'register_number': 6},
#'PushButtons': {'is_enabled': False, 'register_number': 4},
#'Timer1PWM': {'is_enabled': False, 'register_number': 8},
#'Timer3PWM': {'is_enabled': False, 'register_number': 9},


class VersionInfoIface(abc.ABC):
    """
    Check the Controller Version

    Required: True

    Capability Identifier: 'VersionInfo'
    """

    @abc.abstractmethod
    def version(self):
        """
        Return the major and minor version of the software running on the controller
        as a tuple.
        """
        pass


class BatteryVoltageReaderIface(abc.ABC):
    """
    Read the Battery Voltage

    Required: False

    Capability Identifier: 'BatteryVoltageReader'
    """

    @abc.abstractmethod
    def millivolts(self):
        """
        Return the voltage of the battery (in millivolts) connected to the controller.
        Reminder: 1000 millivolts = 1 volt
        """
        pass


class Buzzer(abc.ABC):
    """
    Play Music!

    Required: False

    Capability Identifier: 'Buzzer'
    """

    @abc.abstractmethod
    def is_currently_playing(self):
        """
        Return true if the buzzer is currently playing music.
        Return false if the buzzer is not. You cannot play new
        music while the buzzer is currently playing music, so
        you can use this method to check.
        """
        pass

    @abc.abstractmethod
    def wait(self):
        """
        Block until the buzzer is not playing music anymore.
        """
        pass

    @abc.abstractmethod
    def play(self, notes="o4l16ceg>c8"):
        """
        Tell the controller to play the notes described by the `notes` parameter.
        If the controller is already playing notes, this function will wait for it
        to finish then will play _these_ `notes`. (If the current notes do not finish
        within 10 seconds, this function will give up and raise and error.)
        """
        pass


class Gyroscope:
    """
    Query the Gyroscope Sensor

    Required: False

    Capability Identifier: 'Gyroscope'
    """

    @i2c_retry(N_I2C_TRIES)
    def read(self):
        """
        Read an (x, y, z) tuple-of-floats from one of the controller's components.
        E.g. Read from the Accelerometer, Gyroscope, or Magnetometer.
        """

