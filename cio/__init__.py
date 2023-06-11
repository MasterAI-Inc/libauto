###############################################################################
#
# Copyright (c) 2017-2022 Master AI, Inc.
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from Master AI, Inc.
#
###############################################################################

"""
This package contains the interface to your device's controller(s).

Its name is CIO (Controller Input/Output).
"""

import abc


class CioRoot(abc.ABC):
    """
    This is the front-door interface of the Controller IO ("cio"). You begin
    by `init()`ing the controller, and if successful, you may then `acquire()`
    and `release()` components which are provided by the controller.
    """

    @abc.abstractmethod
    async def init(self):
        """
        Initialize the controller. If successful, this method returns a list
        of capability ids (each capability id is a string). Else, this method
        throws an exception (e.g. if the proper controller is not attached).
        Each of the returned capability ids may be used to "acquire" an interface
        to the corresponding component on the controller via the `acquire()`
        method.
        """
        pass

    @abc.abstractmethod
    async def acquire(self, capability_id):
        """
        Acquire the component whose capability id is `capability_id`.
        This method returns a *new* object which implements the capability's
        interface. Once you are finished using the acquired component,
        you should "release" it by passing the interface to the `release()`
        method. Implementations of this method *must* return a new object
        on each invocation (this is a limitation due to how the CIO RPC server
        works).
        """
        pass

    @abc.abstractmethod
    async def release(self, capability_obj):
        """
        Release a previously acquired capability object. You should
        pass the _actual_ object which was returned by the `acquire()`
        method. This method returns `None`.
        """
        pass

    @abc.abstractmethod
    async def close(self):
        """
        Cleanly close the connection to the controller. All acquired
        component interfaces will be released (thus their corresponding
        objects will become stale and should not be used further).
        You may safely re-`init()` if needed to continue using it.
        """
        pass


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


class CredentialsIface(abc.ABC):
    """
    Store and retrieve various authentication details.

    Required: True

    Capability Identifier: 'Credentials'
    """

    @abc.abstractmethod
    async def get_labs_auth_code(self):
        """
        Return the stored authentication code.
        This authentication code is used to authenticate
        with the Labs servers.
        """
        pass

    @abc.abstractmethod
    async def set_labs_auth_code(self, auth_code):
        """
        Set (and save) the authentication code.
        Might allow only a single write. Returns True/False if write was successful.
        """
        pass

    @abc.abstractmethod
    async def get_jupyter_password(self):
        """
        Return the Jupter password.
        This password will be used by Jupyter to protect
        network access.
        """
        pass

    @abc.abstractmethod
    async def set_jupyter_password(self, password):
        """
        Set (and save) the Jupter password.
        Might allow only a single write. Returns True/False if write was successful.
        """
        pass


class CameraIface(abc.ABC):
    """
    Capture frames from the on-board camera.

    Required: True

    Capability Identifier: 'Camera'
    """

    @abc.abstractmethod
    async def capture(self):
        """
        Capture and return one frame.
        """
        pass


class LoopFrequencyIface(abc.ABC):
    """
    Read the Controller's Loop Frequency (in Hz)

    Required: False

    Capability Identifier: 'LoopFrequency'
    """

    @abc.abstractmethod
    async def read(self):
        """
        Returns the loop frequency of the microcontroller (in Hz).
        """
        pass


class PowerIface(abc.ABC):
    """
    Read the Battery Voltage

    Required: True

    Capability Identifier: 'Power'
    """

    @abc.abstractmethod
    async def state(self):
        """
        Return the state of the power of this device.
        Returns a string, one of:
         - 'battery'  : The device is running on battery power.
         - 'wall'     : The device is running on "wall" power (aka, has external power in some way).
         - 'charging' : The device is charging its battery, which implies "wall" power as well.
        """
        pass

    @abc.abstractmethod
    async def millivolts(self):
        """
        Return the voltage of the battery (in millivolts) connected to the controller.
        Reminder: 1000 millivolts = 1 volt
        """
        pass

    @abc.abstractmethod
    async def estimate_remaining(self, millivolts=None):
        """
        Given the battery voltage of `millivolts`, estimate of run-time remaining of
        the batter (in minutes) and the percentage remaining of the battery (an
        integer from 0 to 100). Return a two-tuple of `(minutes, percentage)`.
        If you pass `millivolts=None`, the battery's current millivolts reading will
        be queried and used.
        """
        pass

    @abc.abstractmethod
    async def should_shut_down(self):
        """
        Return True if the host device should shut down. The host
        can poll this function (suggest once per 200-500ms) to know
        when it needs to shut down. Two reasons for shutting down:
         1. The power switch was triggered so the whole device will
            soon loose power.
         2. The battery is dangerously low and will drop out soon,
            so the host should shut down immediately to be safe.
        """
        pass

    @abc.abstractmethod
    async def shut_down(self):
        """
        Instruct the device to shut itself down.
        """
        pass

    @abc.abstractmethod
    async def reboot(self):
        """
        Instruct the device to reboot itself.
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


class MagnetometerIface(abc.ABC):
    """
    Query the Magnetometer Sensor

    Required: False

    Capability Identifier: 'Magnetometer'
    """

    @abc.abstractmethod
    async def read(self):
        """
        Read an (x, y, z) tuple-of-floats from the Magnetometer.
        """
        pass


class AhrsIface(abc.ABC):
    """
    Query the computed AHRS ("Attitude and Header Reference System").
    https://en.wikipedia.org/wiki/Attitude_and_heading_reference_system

    Required: False

    Capability Identifier: 'AHRS'
    """

    @abc.abstractmethod
    async def read(self):
        """
        Get the current (roll, pitch, yaw) tuple-of-floats of the device.
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

    @abc.abstractmethod
    async def set_brightness(self, brightness):
        """
        Set the brightness of the LEDs, in the range [0-255].
        Raises if not supported by the hardware you have.
        Setting `brightness=0` means set the brightness to the
        default value.
        """
        pass


class AdcIface(abc.ABC):
    """
    Query the Analog-to-Digital Converter (ADC)

    Required: False

    Capability Identifier: 'ADC'
    """

    @abc.abstractmethod
    async def num_pins(self):
        """
        Return the number of ADC pins on this controller.
        """

    @abc.abstractmethod
    async def read(self, index):
        """
        Read and return the voltage (in Volts) of the ADC pin
        at index `index`. The first pin is index-0 (i.e.
        zero-based indexing). Call `num_pins()` to know the
        index range.
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
        Tell the car to begin powering its motors (the main motor and the servo).
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
    async def get_safe_throttle(self):
        """
        Return the range of the "safe" throttle values, where "safe" means
        the resulting speed will be slow enough for the typical indoor classroom
        environment. A two-tuple is returned `(min_throttle, max_throttle)`.

        **Disclaimer:** Any and all movement of the vehicle can result in injury
                        if proper safety precautions are not taken. It is the
                        responsibility of the user to use the device in a safe
                        manner at all times.
        """
        pass

    @abc.abstractmethod
    async def set_safe_throttle(self, min_throttle, max_throttle):
        """
        Store a new "safe" throttle range; will be returned by `get_safe_throttle()`
        on subsequent calls.
        """
        pass

    @abc.abstractmethod
    async def off(self):
        """
        Turn off the car's motors.
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
    async def status(self):
        """
        Check the status of the calibration process.
        Returns the identifier of the current step.
        Status identifiers may be integers or strings.
        Each controller has its own identifiers and
        its own meaning for each identifier. You must
        refer to the specific controller's documentation
        to understand what each status identifier means.
        The only common identifiers between all controllers
        are the following:
         - The integer 0 means the calibration process
           has not started.
         - The integer -1 means the calibration process
           was started and has now finished.
        """
        pass

    @abc.abstractmethod
    async def script_name(self):
        """
        Return the name of the script used
        for calibrating this device. On
        a properly configured system, this
        script will be somewhere in the
        user's PATH.
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
    async def set_pid(self, p, i, d, error_accum_max=0.0, save=False):
        """
        Sets P, I, and D. If the device has no default values for this PID
        loop, you should be sure to call this method `set_pid()` before calling
        `enable()`.

        If `save` is set, then these values will be saved to persistent storage
        and used as the defaults in the future.

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
    Control the Device's Steering with a PID Loop

    Required: False

    Capability Identifier: 'PID_steering'
    """
    pass   # <-- See abstract methods of `PidIface`


class CarControlIface(abc.ABC):
    """
    Uses `CarMotors`, `PID_steering`, `Gyroscope_accum`, and `Encoders`
    to drive a car-form-factor robot with high-level commands.

    Required: False

    Capability Identifier: 'CarControl'
    """

    @abc.abstractmethod
    async def on(self):
        """
        Tell the car to begin powering its motors (the main motor and the servo)
        and active its other sensors (gyroscope, PID steering, encoders, if
        present).
        """
        pass

    @abc.abstractmethod
    async def straight(self, throttle, sec=None, cm=None):
        """
        Drive the car *straight* at the given `throttle` value.

        This function uses the car's gyroscope (if present) to continually keep
        the car pointing in the same direction in which it started (aka, "active
        steering stabilization").

        If `sec` is provided (not None), then the car will drive for that many
        seconds. Else, if `cm` is provided (not None), then the car will drive
        for that many centimeters (only works on cars with wheel encoders). It
        is an error to pass neither `sec` nor `cm`. It is also an error to pass
        both `sec` and `cm`.
        """
        pass

    @abc.abstractmethod
    async def drive(self, steering, throttle, sec=None, deg=None):
        """
        Drive the car at the given wheel `steering` and at the given `throttle`
        value. See `CarMotorsIface`s `set_steering()` and `set_throttle()`
        for details of the values these parameters can take.

        If `sec` is provided (not None), then the car will drive for that many
        seconds. Else, if `deg` is provided (not None), then the car will drive
        until it rotates by that many degrees (if provided, `deg` must be a
        positive value; this functionality only works for cars with gyroscopes).
        It is an error to pass neither `sec` nor `deg`. It is also an error to
        pass both `sec` and `deg`.

        Note: If you use this function to drive the car *straight*
              (i.e. `steering=0`), the car may still veer because this function
              does _not_ actively stabilize for going straight. If you desire
              active stabilization for going straight, use the `straight()`
              method instead.
        """
        pass

    @abc.abstractmethod
    async def off(self):
        """
        Turn off the car's motors and disable any other sensors that were being
        used.
        """
        pass


class LidarIface(abc.ABC):
    """
    Query the Lidar system of your device!

    Required: False

    Capability Identifier: 'Lidar'
    """

    @abc.abstractmethod
    async def single(self, theta=0, phi=90):
        """
        Query in a single direction, denoted by `theta` and `phi`
        (using spherical coordinates), where the origin is the
        Lidar sensor's current position.

        Parameters:

         - `theta`: rotation (in degrees) in the horizontal plane;
           `theta=0` points straight "forward"; positive `theta` is
           to the left; negative `theta` is to the right.

         - `phi`: rotation (in degrees) away from the vertical axis;
           `phi=0` points straight "up" the vertical axis; positive `phi`
           moves off the vertical axis; `phi=90` lies on the horizontal
           plane; `phi=180` points opposite the vertical axis ("down").

        Returns `r` which is the distance (in meters) to the closest object
        in the direction denoted by `theta` and `phi`. Returns `r = None`
        if no object was detected.
        """
        pass

    @abc.abstractmethod
    async def sweep(self, theta_1=90, phi_1=90, theta_2=-90, phi_2=90):
        """
        Sweep the sensor from (`theta_1`, `phi_1`) to (`theta_2`, `phi_2`)
        and query 16 times during the sweep motion. The sensor will query
        at equal intervals along the sweep path, where the first query
        happens at (`theta_1`, `phi_1`) and the last query happens at
        (`theta_2`, `phi_2`).

        Returns a list of 16 values of `r`.

        See `single()` for a description of `theta`, `phi`, and `r`.

        Using this method `sweep()` is more efficient than calling `single()`
        over-and-over.
        """
        pass


class CompassIface(abc.ABC):
    """
    Query your device's Compass!

    Required: False

    Capability Identifier: 'Compass'
    """

    @abc.abstractmethod
    async def query(self):
        """
        Query the Compass sensor.

        Returns `theta`, a single angle (in degrees) representing your
        device's deviation from magnetic north.
         - `theta = 0` means your device is pointing directly north.
         - `theta = 90` means your device is pointing directly west.
         - `theta = 180` means your device is pointing directly south.
         - `theta = 270` means your device is pointing directly east.
        """
        pass

    @abc.abstractmethod
    async def heading(self):
        """
        Query the Compass sensor and return a true heading of your device.

        **ONLY AVAILABLE ON VIRTUAL DEVICES!**

        Real-world compasses cannot give you this information, but the
        "virtual" compass can. :)

        Returns a tuple (`theta`, `phi`) describing the true heading of
        your device. `theta` is an angle (in degrees) of your device's
        rotation in the world's horizontal plane. `phi` is an angle (in
        degrees) of your device's rotation away from the vertical axis.
        See `Lidar.single()` for more info on the concept of `theta` and
        `phi` and on the concept of spherical coordinates.
        """
        pass


class GpsIface(abc.ABC):
    """
    Query your device's GPS sensor!

    Required: False

    Capability Identifier: 'GPS'
    """

    @abc.abstractmethod
    async def query(self):
        """
        Query the GPS sensor. The return value depends on the type of device
        you are using:

        For *physical* devices, the return value is a point using the
        *Geographic coordinate system*, thus it is a three-tuple:
            (`latitude`, `longitude`, `altitude`)

        For *virtual* devices, the return value is a point using the
        *Cartesian coordinate system*, thus it is a three-tuple:
            (`x`, `y`, `z`)
        """
        pass


class ReconIface(abc.ABC):
    """
    Your device's Reconnaissance sensor (*virtual* devices only)

    Required: False

    Capability Identifier: 'Recon'
    """

    @abc.abstractmethod
    async def query(self, theta_1=90, theta_2=-90, r=10000):
        """
        Detect enemy devices within a certain space around your
        device, as defined by `theta_1`, `theta_2`, and `r`.

        The space queried ranges in your device's horizontal
        plane from `theta_1` to `theta_2` (both in degrees)
        and extends `r` meters away from your device.

        These "theta" values (in degrees) affect the sensor's
        detection space around your device's horizontal plane:
         - `theta = 0` is "forward" of your device
         - `theta = 90` is "directly left"
         - `theta = -90` is "directly right"

        For example, querying with `theta_1 = 45` and `theta_2 = -45`
        will query a 90-degree circular sector in front of your device.

        Another example, querying with `theta_1 = 0` and `theta_2 = 360`
        will query for *all* devices near you, no matter what angle they
        are from you.

        Another example, querying with `theta_1 = 90` and `theta_2 = 270`
        will query in the half-circle space "behind" your device.

        The `r` value (a distance in meters) affects the sensor's query
        radius from your device. E.g. `r = 100` will detect enemy devices
        within 100 meters of your device.

        Note: To precisely locate an enemy, you can binary search the
              `theta_*` space, then binary search the `r` space.

        This query returns a list of device VINs which were found in the
        queried space. An empty list is returned if no devices are found.
        """
        pass


class WeaponsIface(abc.ABC):
    """
    Your device's Weapons system (*virtual* devices only)

    Required: False

    Capability Identifier: 'Weapons'
    """

    @abc.abstractmethod
    async def fire(self, theta=0, phi=90, velocity=40):
        """
        Fire your device's default weapon in the direction
        defined by `theta` and `phi` (both in degrees) and
        with a velocity of `velocity` (in meters/second).

        See `LidarIface.single()` for a description of `theta`
        and `phi`.
        """
        pass


class PhysicsClientIface(abc.ABC):
    """
    Instruct the physics client. This is only used for virtual devices.

    Required: False

    Capability Identifier: 'PhysicsClient'
    """

    @abc.abstractmethod
    async def control(self, msg):
        """
        Pass this control-message to the physics client.
        """
        pass

    @abc.abstractmethod
    async def wait_tick(self):
        """
        Wait until the next physics engine "tick". The physics
        engine does 20 updates per second (each is called a "tick"),
        and it sends a message to us after each update. Thus, this
        method simply waits for the next message to arrive and then
        returns. You can use this method to do computation in lock-step
        with the physics engine, as it is silly to do certain things
        faster than the physics engine (e.g. querying GPS) since updates
        only happen after each "tick".
        """
        pass

    @abc.abstractmethod
    async def sleep(self, seconds):
        """
        Sleeps for approximately `seconds` by counting "ticks" from the
        physics engine. This provides a way to sleep in lock-step with
        the physics engine to minimize drift.
        """
        pass

