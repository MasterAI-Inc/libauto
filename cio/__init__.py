"""
This package contains the interface to your robot's microcontroller(s).

It's name is CIO (Controller Input/Output).
"""

import abc


class VersionInfoIface(abc.ABC):
    """
    Check the Controller Version

    Required: True

    Capability Identifier: 'VersionInfo'
    """

    @abc.abstractmethod
    async def name(self):
        """
        Return the name of the controller (e.g. the product
        name and model number of the robot) as a string.
        There is no specific format for this string, it is
        intended to by human readable.
        """
        pass

    @abc.abstractmethod
    async def version(self):
        """
        Return the major and minor version of the software running on the controller
        as a two-tuple.
        """
        pass


class LoopFrequencyIface(abc.ABC):
    """
    Read the Controller's Loop Frequency (in Hz)

    Required: True

    Capability Identifier: 'LoopFrequency'
    """

    @abc.abstractmethod
    async def read(self):
        """
        Returns the loop frequency of the microcontroller (in Hz).
        """
        pass


class BatteryVoltageReaderIface(abc.ABC):
    """
    Read the Battery Voltage

    Required: True

    Capability Identifier: 'BatteryVoltageReader'
    """

    @abc.abstractmethod
    async def millivolts(self):
        """
        Return the voltage of the battery (in millivolts) connected to the controller.
        Reminder: 1000 millivolts = 1 volt
        """
        pass

    @abc.abstractmethod
    async def minutes(self):
        """
        Estimate of time remaining (in minutes).
        Return a two-tuple of the 95% confidence interval.
        """
        pass


class BuzzerIface(abc.ABC):
    """
    Play Music!

    Required: False

    Capability Identifier: 'Buzzer'
    """

    @abc.abstractmethod
    async def is_currently_playing(self):
        """
        Return true if the buzzer is currently playing music.
        Return false if the buzzer is not. You cannot play new
        music while the buzzer is currently playing music, so
        you can use this method to check.
        """
        pass

    @abc.abstractmethod
    async def wait(self):
        """
        Block until the buzzer is not playing music anymore.
        """
        pass

    @abc.abstractmethod
    async def play(self, notes="o4l16ceg>c8"):
        """
        Tell the controller to play the notes described by the `notes` parameter.
        If the controller is already playing notes, this function will wait for it
        to finish then will play _these_ `notes`.
        """
        pass


class GyroscopeIface(abc.ABC):
    """
    Query the Gyroscope Sensor

    Required: False

    Capability Identifier: 'Gyroscope'
    """

    @abc.abstractmethod
    async def read(self):
        """
        Read an (x, y, z) tuple-of-floats from the Gyroscope.
        """
        pass


class GyroscopeAccumIface(abc.ABC):
    """
    Query the Gyroscope Sensor with Internally-Accumulated Values

    Required: False

    Capability Identifier: 'Gyroscope_accum'
    """

    @abc.abstractmethod
    async def reset(self):
        """
        Reset the (x, y, z) accumulators back to zero.
        """
        pass

    @abc.abstractmethod
    async def read(self):
        """
        Read the accumulated (x, y, z) tuple-of-floats from the Gyroscope.
        """
        pass


class AccelerometerIface(abc.ABC):
    """
    Query the Accelerometer Sensor

    Required: False

    Capability Identifier: 'Accelerometer'
    """

    @abc.abstractmethod
    async def read(self):
        """
        Read an (x, y, z) tuple-of-floats from the Accelerometer.
        """
        pass


class PushButtonsIface(abc.ABC):
    """
    Query the Tactile Push Button(s)

    Required: False

    Capability Identifier: 'PushButtons'
    """

    @abc.abstractmethod
    async def num_buttons(self):
        """
        Return the number of buttons on the device.
        """
        pass

    @abc.abstractmethod
    async def button_state(self, button_index):
        """
        Return the state of the button at the given index (zero-based).
        Returns a tuple of (num_presses, num_releases, is_currently_pressed)
        which are of types (int, int, bool).
        """
        pass

    @abc.abstractmethod
    async def get_events(self):
        """
        Return a list of buttons events that have happened since
        the last call this method. The returned list will be empty
        if no events have transpired.
        """
        pass

    @abc.abstractmethod
    async def wait_for_event(self):
        """
        Wait for the next event, and return it once it occurs.
        """
        pass

    @abc.abstractmethod
    async def wait_for_action(self, action='pressed'):
        """
        Wait for a certain button action to happen.

        The `action` may be one of:
            - "pressed" : Wait for a button to be pressed.
                          This is the default.
            - "released": Wait for a button to be released.
            - "any"     : Wait for either a button to be pressed or released,
                          whichever happens first.

        A two-tuple is returned `(button_index, action)`, where
        `button_index` is the zero-based index of the button on which
        the action occurred, and `action` is either "pressed" or "released".
        """
        pass


class LEDsIface(abc.ABC):
    """
    Set LED State

    Required: False

    Capability Identifier: 'LEDs'
    """

    @abc.abstractmethod
    async def led_map(self):
        """
        Return identifiers and descriptions of the LEDs
        available on this controller as a dictionary.
        The keys are the identifiers used to control the LEDs
        via the `set_led()` method.
        """
        pass

    @abc.abstractmethod
    async def set_led(self, led_identifier, val):
        """
        Set the LED on/off value.
        """
        pass

    @abc.abstractmethod
    async def set_many_leds(self, id_val_list):
        """
        Pass a list of tuples, where each tuple is an LED identifier
        and the value you want it set to.
        """
        pass

    @abc.abstractmethod
    async def mode_map(self):
        """
        Return identifiers and descriptions of the LED modes
        that are available as a dictionary.
        The keys are the identifiers used to set the mode
        via the `set_mode()` method.
        """
        pass

    @abc.abstractmethod
    async def set_mode(self, mode_identifier):
        """
        Set the `mode` of the LEDs.
        Pass `None` to clear the mode, thereby commencing
        basic on/off control via the `set_led()` method.
        """
        pass


class PhotoresistorIface(abc.ABC):
    """
    Query the Photoresistor

    Required: False

    Capability Identifier: 'Photoresistor'
    """

    @abc.abstractmethod
    async def read(self):
        """
        Read the voltage of the photoresistor pin, and read
        the computed resistance of the photoresistor. Return
        both as a two-tuple `(millivolts, ohms)`.
        """
        pass

    @abc.abstractmethod
    async def read_millivolts(self):
        """
        Read the raw voltage of the photoresistor pin.
        """
        pass

    @abc.abstractmethod
    async def read_ohms(self):
        """
        Read the resistance of the photoresistor (in ohms). The photoresistor's
        resistance changes depending on how much light is on it, thus the name!
        """
        pass


class EncodersIface(abc.ABC):
    """
    Query the Quadrature Encoder(s)

    Required: False

    Capability Identifier: 'Encoders'
    """

    @abc.abstractmethod
    async def num_encoders(self):
        """
        Return the number of Quadrature Encoders on this controller.
        """
        pass

    @abc.abstractmethod
    async def enable(self, encoder_index):
        """
        Enable an encoder. The first encoder is index-0.
        """
        pass

    @abc.abstractmethod
    async def read_counts(self, encoder_index):
        """
        Read the counts of the encoder. The first encoder is index-0.
        The count is reset to zero when the encoder is enabled.

        A three-tuple is returned:
         - Number of "clicks" (a signed value).
         - Pin A change count (an unsigned, positive value).
         - Pin B change count (an unsigned, positive value).
        """
        pass

    @abc.abstractmethod
    async def read_timing(self, encoder_index):
        """
        Return the number of microseconds that each of the two pins on the first
        encoder (e1) are high (i.e. the duration the pin stays in the high state).
        This can be used to read a PWM signal (assuming the PWM signal has a known,
        fixed frequency). If the pin has not gone high-then-low recently (within
        the last half-second), the value returned here will be 0 to indicate
        it is not presently known (i.e. the PWM signal is not currently coming
        through). A two-tuple is returned by this method: `(pin_a_usecs, pin_b_usecs)`.
        Recall: 1000000 microseconds = 1 second
        """
        pass

    @abc.abstractmethod
    async def disable(self, encoder_index):
        """
        Disable an encoder. The first encoder is index-0.
        """
        pass


class CarMotorsIface(abc.ABC):
    """
    Control the Robots which are in the "Car Form Factor"

    Required: False

    Capability Identifier: 'CarMotors'
    """

    @abc.abstractmethod
    async def on(self):
        """
        Tell the car to begin controlling the motors (the main motor and the servo).
        The car will use the most recently set PWM signal parameters, or it will
        read from its EEPROM to get those values.
        """
        pass

    @abc.abstractmethod
    async def set_steering(self, steering):
        """
        Set the car's steering (i.e. move the servo).

        Pass a value in the range [-45, 45] to represent [full-right, full-left].
        """
        pass

    @abc.abstractmethod
    async def set_throttle(self, throttle):
        """
        Set the car's throttle (i.e. power send to the main motor).

        Pass a value in the range [-100, 100] to represent [full-reverse, full-forward].
        """
        pass

    @abc.abstractmethod
    async def off(self):
        """
        Turn off the car's PWM motor control.
        """
        pass


class PWMsIface(abc.ABC):
    """
    Control the PWM-capable Pins on the Controller

    Required: False

    Capability Identifier: 'PWMs'
    """

    @abc.abstractmethod
    async def num_pins(self):
        """
        Return the number of pins which support PWM on this controller.
        """
        pass

    @abc.abstractmethod
    async def enable(self, pin_index, frequency, duty=0):
        """
        Enable PWM on a given pin at a given frequency (in Hz). The first pin is index-0.
        An error will be thrown if the desired frequency is not possible. The duty cycle
        will be 0% by default (pass the `duty` parameter to enable it at a non-zero duty
        cycle). Call `set_duty()` to change the duty cycle of this pin once it is enabled.

        **NOTE**: On most microcontrollers, there will be two or more pins that are driven
                  by the same internal timer, thus the frequency of those pins must be the
                  same. If this is the case and you try to set different frequencies, you
                  will get an exception.
        """
        pass

    @abc.abstractmethod
    async def set_duty(self, pin_index, duty):
        """
        Set the duty cycle of the pin's PWM output. The duty
        cycle is given as a percentage in the range [0.0, 100.0].
        You may pass integer or float values. The controller
        will match the desired duty cycle as closely as possible
        subject to its internal resolution.
        """
        pass

    @abc.abstractmethod
    async def disable(self, pin_index):
        """
        Disable PWM on a given pin. The first pin is index-0.
        """
        pass


class CalibratorIface(abc.ABC):
    """
    Instruct the Controller to Start the Calibration Process

    Required: False

    Capability Identifier: 'Calibrator'
    """

    @abc.abstractmethod
    async def start(self):
        """
        Instruct the controller to start its calibration process.
        """
        pass

    @abc.abstractmethod
    async def check(self):
        """
        Check if the calibration process is running.
        Returns True if the controller is currently
        running its calibration, False otherwise.
        """
        pass


class PidIface(abc.ABC):
    """
    Control a PID Loop on the Controller

    THIS INTERFACE IS GENERIC; SPECIFIC PID LOOPS WILL
    INHERIT FROM IT AND IMPLEMENT IT. FOR EXAMPLE, SEE:
        `PID_steering`
    """

    @abc.abstractmethod
    async def set_pid(self, p, i, d, error_accum_max=0.0):
        """
        Sets P, I, and D. It is best to do this before enabling the loop.

        `error_accum_max` is the max accumulated error that will be accumulated.
        This is a common thing that is done to tame the PID loop and not crazy overshoot
        due to `I` accumulating unreasonably high. Zero means there is no limit.
        """
        pass

    @abc.abstractmethod
    async def set_point(self, point):
        """
        Set the sensor's "set point". The actuator will be controlled so that
        the sensor stays at the "set point".
        """
        pass

    @abc.abstractmethod
    async def enable(self, invert_output=False):
        """
        Enable the PID loop within the controller (i.e. begin to drive the actuator to
        the set point).

        You should call `set_pid()` and `set_point()` before `enable()` so that
        the actuator is properly driven immediately upon being enabled. Once
        enabled, you can repeatedly call `set_point()` as needed.
        """
        pass

    @abc.abstractmethod
    async def disable(self):
        """
        Disable the PID loop within the controller (i.e. stop driving the actuator).
        """
        pass


class PidSteeringIface(PidIface):
    """
    Control the Car's Steering with a PID Loop

    Required: False

    Capability Identifier: 'PID_steering'
    """
    pass   # <-- See abstract methods of `PidIface`

