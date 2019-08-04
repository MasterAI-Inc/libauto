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
This module provides easy helper functions which abstract the behavior of
the car to a very high level. These functions are intended to be used by
beginners. All of the functionality in these helper functions can be
recreated using lower-level abstractions exposed by the other modules of
libauto.

These helper functions, when invoked, each print info about what they are
doing. Normally a library should _not_ print anything, but we make an
exception for these functions because they are intended to be used by
beginners who are new to programming, and the printouts are helpful for
the beginners to see what is happening. The other modules of libauto
do not print.
"""

from auto import print_all as print  # override the build-in `print()`

import time


def forward(duration=1.0, verbose=True):
    """
    Drive the car forward for `duration` seconds.
    """
    from car import motors
    if duration > 5.0:
        print("Error: The duration exceeds 5 seconds; will reset to 5 seconds.")
        duration = 5.0
    if verbose:
        print("Driving forward for {} seconds.".format(duration))
    if duration <= 0.0:
        return
    motors.straight(motors.CAR_THROTTLE_FORWARD_SAFE_SPEED, duration, invert_output=False)


def reverse(duration=1.0, verbose=True):
    """
    Drive the car in reverse for `duration` seconds.
    """
    from car import motors
    if duration > 5.0:
        print("Error: The duration exceeds 5 seconds; will reset to 5 seconds.")
        duration = 5.0
    if verbose:
        print("Driving in reverse for {} seconds.".format(duration))
    if duration <= 0.0:
        return
    motors.straight(motors.CAR_THROTTLE_REVERSE_SAFE_SPEED, duration, invert_output=True)


def left(duration=1.0, verbose=True):
    """
    Drive the car forward and left for `duration` seconds.
    """
    from car import motors
    if duration > 5.0:
        print("Error: The duration exceeds 5 seconds; will reset to 5 seconds.")
        duration = 5.0
    if verbose:
        print("Driving left for {} seconds.".format(duration))
    if duration <= 0.0:
        return
    motors.drive(45.0, motors.CAR_THROTTLE_FORWARD_SAFE_SPEED, duration)


def right(duration=1.0, verbose=True):
    """
    Drive the car forward and right for `duration` seconds.
    """
    from car import motors
    if duration > 5.0:
        print("Error: The duration exceeds 5 seconds; will reset to 5 seconds.")
        duration = 5.0
    if verbose:
        print("Driving right for {} seconds.".format(duration))
    if duration <= 0.0:
        return
    motors.drive(-45.0, motors.CAR_THROTTLE_FORWARD_SAFE_SPEED, duration)


def pause(duration=1.0, verbose=True):
    """
    Pause the car's code for `duration` seconds.
    """
    if verbose:
        print("Pausing for {} seconds.".format(duration))
    time.sleep(duration)


def capture(num_frames=1, verbose=True):
    """
    Capture `num_frames` frames from the car's camera and return
    them as a numpy ndarray.
    """
    from auto import camera
    return camera.capture(num_frames, verbose)


def plot(frames, also_stream=True, verbose=True, **fig_kwargs):
    """
    Plot the given `frames` (a numpy ndarray) into a matplotlib figure,
    returning the figure object which can be shown. This function by
    default also streams the image to your `labs` account.

    The `frames` parameter must be a numpy ndarray with one of the
    following shapes:
        - (n, h, w, 3)   meaning `n` 3-channel RGB images of size `w`x`h`
        - (n, h, w, 1)   meaning `n` 1-channel gray images of size `w`x`h`
        -    (h, w, 3)   meaning a single 3-channel RGB image of size `w`x`h`
        -    (h, w, 1)   meaning a single 1-channel gray image of size `w`x`h`
        -    (h, w)      meaning a single 1-channel gray image of size `w`x`h`
    """
    from auto import frame_streamer
    return frame_streamer.plot(frames, also_stream, verbose, **fig_kwargs)


def stream(frame, to_console=True, to_labs=False, verbose=True):
    """
    Stream the given `frame` (a numpy ndarray) to your car's
    console _and_ (optionally) to your `labs` account to be shown
    in your browser.

    The `frame` parameter must be a numpy ndarray with one of the
    following shapes:
        - (h, w, 3)   meaning a single 3-channel RGB image of size `w`x`h`
        - (h, w, 1)   meaning a single 1-channel gray image of size `w`x`h`
        - (h, w)      meaning a single 1-channel gray image of size `w`x`h`
    """
    from auto import frame_streamer
    return frame_streamer.stream(frame, to_console, to_labs, verbose)


def classify_color(frame, annotate=True, verbose=True):
    """
    Classify the center region of `frame` as having either primarily "red",
    "yellow", or "green, or none of those ("background").

    The `frame` parameter must be a numpy array containing an RGB image.

    Returns a string representing the color found in the center of the
    image, one of "red", "yellow", "green", or "background".
    """
    global COLORCLASSIFIER
    try: COLORCLASSIFIER
    except NameError:
        from auto.models import ColorClassifier
        COLORCLASSIFIER = ColorClassifier()
        if verbose:
            print("Instantiated a ColorClassifier object!")

    p1, p2, classific = COLORCLASSIFIER.classify(frame, annotate=annotate)
    if verbose:
        print("Classified color as '{}'.".format(classific))
    return classific


def detect_faces(frame, annotate=True, verbose=True):
    """
    Detect faces inside of `frame`, and annotate each face.

    The `frame` parameter must be an image as a numpy array either containing
    3-channel RGB values _or_ 1-channel gray values.

    Returns a list of rectangles, where each rectangle is a 4-tuple of:
        (x, y, width, height)
    """
    global FACEDETECTOR
    try: FACEDETECTOR
    except NameError:
        from auto.models import FaceDetector
        FACEDETECTOR = FaceDetector()
        if verbose:
            print("Instantiated a FaceDetector object!")

    faces = FACEDETECTOR.detect(frame, annotate=annotate)
    n = len(faces)
    if verbose:
        print("Found {} face{}.".format(n, 's' if n != 1 else ''))
    return faces


def detect_stop_signs(frame, annotate=True, verbose=True):
    """
    Detect stop signs inside of `frame`, and annotate each stop sign.

    The `frame` parameter must be an image as a numpy array either containing
    3-channel RGB values _or_ 1-channel gray values.

    Returns a list of rectangles, where each rectangle is a 4-tuple of:
        (x, y, width, height)
    """
    global STOPSIGNDETECTOR
    try: STOPSIGNDETECTOR
    except NameError:
        from auto.models import StopSignDetector
        STOPSIGNDETECTOR = StopSignDetector()
        if verbose:
            print("Instantiated a StopSignDetector object!")

    rects = STOPSIGNDETECTOR.detect(frame, annotate=annotate)
    n = len(rects)
    if verbose:
        print("Found {} stop sign{}.".format(n, 's' if n != 1 else ''))
    return rects


def detect_pedestrians(frame, annotate=True, verbose=True):
    """
    Detect pedestrians inside of `frame`, and annotate each pedestrian.

    The `frame` parameter must be an image as a numpy array either containing
    3-channel RGB values _or_ 1-channel gray values.

    Returns a list of rectangles, where each rectangle is a 4-tuple of:
        (x, y, width, height)
    """
    global PEDESTRIANDETECTOR
    try: PEDESTRIANDETECTOR
    except NameError:
        from auto.models import PedestrianDetector
        PEDESTRIANDETECTOR = PedestrianDetector()
        if verbose:
            print("Instantiated a PedestrianDetector object!")

    rects = PEDESTRIANDETECTOR.detect(frame, annotate=annotate)
    n = len(rects)
    if verbose:
        print("Found {} pedestrian{}.".format(n, 's' if n != 1 else ''))
    return rects


def object_location(object_list, frame_shape, verbose=True):
    """
    Calculate the location of the largest object in `object_list`.

    Returns one of: 'frame_left', 'frame_right', 'frame_center', None
    """
    if not object_list:
        if verbose:
            print("Object location is None.")
        return None
    import numpy as np
    areas = [w*h for x, y, w, h in object_list]
    i = np.argmax(areas)
    nearest = object_list[i]
    x, y, w, h = nearest
    x_center = x + w/2.
    if x_center < frame_shape[1]/3.:
        location = 'frame_left'
    elif x_center < 2*frame_shape[1]/3.:
        location = 'frame_center'
    else:
        location = 'frame_right'
    if verbose:
        print("Object location is '{}'.".format(location))
    return location


def object_size(object_list, frame_shape, verbose=True):
    """
    Calculate the ratio of the nearest object's area to the frame's area.
    """
    if not object_list:
        if verbose:
            print("Object area is 0.")
        return 0.0
    areas = [w*h for x, y, w, h in object_list]
    ratio = max(areas) / (frame_shape[0] * frame_shape[1])
    if verbose:
        print("Object area is {}.".format(ratio))
    return ratio


def calibrate():
    """
    Run the end-to-end calibration routine for this car.
    """
    from car import calibration
    calibration.calibrate()


def buzz(notes):
    """
    Play the given `notes` on the device's buzzer.
    """
    from car import buzzer
    buzzer.buzz(notes)


def honk():
    """
    Make a car horn ("HONK") sound.
    """
    from car import buzzer
    buzzer.honk()

