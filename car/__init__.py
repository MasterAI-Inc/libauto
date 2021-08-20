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
This module provides easy helper functions which abstract the behavior of
the car to a very high level. These functions are intended to be used by
beginners. All of the functionality in these helper functions can be
recreated using lower-level abstractions provided by the other modules of
libauto.

These helper functions, when invoked, each print info about what they are
doing. Normally a library should _not_ print anything, but we make an
exception for these functions because they are intended to be used by
beginners who are new to programming, and the printouts are helpful for
the beginners to see what is happening. The other modules of libauto
do not print.
"""

from auto import print_all as print  # override the build-in `print()`
from auto import _ctx_print_all
from auto import IS_VIRTUAL
import time


def forward(sec=None, cm=None, verbose=True):
    """
    Drive the car forward for `sec` seconds or `cm` centimeters (passing in both
    will raise an error). If neither is passed in, the car will drive for 1 second.
    """
    from car import motors

    if sec is not None and cm is not None:
        _ctx_print_all("Error: Please specify duration (sec) OR distance (cm) - not both.")
        return

    if sec is None and cm is None:
        sec = 1.0

    if sec is not None:
        if sec > 5.0:
            _ctx_print_all("Error: The duration (sec) exceeds 5 seconds; will reset to 5 seconds.")
            sec = 5.0
        if sec <= 0.0:
            return
        if verbose:
            _ctx_print_all("Driving forward for {} seconds.".format(sec))

    if cm is not None:
        if cm > 300.0:
            _ctx_print_all("Error: The distance (cm) exceeds 300 cm (~10 feet); will reset to 300 cm.")
            cm = 300.0
        if cm <= 0.0:
            return
        if verbose:
            _ctx_print_all("Driving forward for {} centimeters.".format(cm))

    motors.straight(motors.safe_forward_throttle(), sec, cm)


def reverse(sec=None, cm=None, verbose=True):
    """
    Drive the car in reverse for `sec` seconds or `cm` centimeters (passing in both
    will raise an error). If neither is passed in, the car will drive for 1 second.
    """
    from car import motors

    if sec is not None and cm is not None:
        _ctx_print_all("Error: Please specify duration (sec) OR distance (cm) - not both.")
        return

    if sec is None and cm is None:
        sec = 1.0

    if sec is not None:
        if sec > 5.0:
            _ctx_print_all("Error: The duration (sec) exceeds 5 seconds; will reset to 5 seconds.")
            sec = 5.0
        if sec <= 0.0:
            return
        if verbose:
            _ctx_print_all("Driving in reverse for {} seconds.".format(sec))

    if cm is not None:
        if cm > 300.0:
            _ctx_print_all("Error: The distance (cm) exceeds 300 cm (~10 feet); will reset to 300 cm.")
            cm = 300.0
        if cm <= 0.0:
            return
        if verbose:
            _ctx_print_all("Driving in reverse for {} centimeters.".format(cm))

    motors.straight(motors.safe_reverse_throttle(), sec, cm, invert_output=True)


def left(sec=None, deg=None, verbose=True):
    """
    Drive the car forward and left for `sec` seconds or `deg` degrees (passing in both
    will raise an error). If neither is passed in, the car will drive for 1 second.
    """
    from car import motors

    if sec is not None and deg is not None:
        _ctx_print_all("Error: Please specify duration (sec) OR degrees (deg) - not both.")
        return

    if sec is None and deg is None:
        sec = 1.0

    if sec is not None:
        if sec > 5.0:
            _ctx_print_all("Error: The duration (sec) exceeds 5 seconds; will reset to 5 seconds.")
            sec = 5.0
        if sec <= 0.0:
            return
        if verbose:
            _ctx_print_all("Driving left for {} seconds.".format(sec))

    if deg is not None:
        if deg > 360.0:
            _ctx_print_all("Error: The degrees (deg) exceeds 360; will reset to 360.")
            deg = 360.0
        if deg <= 0.0:
            return
        if verbose:
            _ctx_print_all("Driving left for {} degrees.".format(deg))

    motors.drive(45.0, motors.safe_forward_throttle(), sec, deg)


def right(sec=None, deg=None, verbose=True):
    """
    Drive the car forwad and right for `sec` seconds or `deg` degrees (passing in both
    will raise an error). If neither is passed in, the car will drive for 1 second.
    """
    from car import motors

    if sec is not None and deg is not None:
        _ctx_print_all("Error: Please specify duration (sec) OR degrees (deg) - not both.")
        return

    if sec is None and deg is None:
        sec = 1.0

    if sec is not None:
        if sec > 5.0:
            _ctx_print_all("Error: The duration (sec) exceeds 5 seconds; will reset to 5 seconds.")
            sec = 5.0
        if sec <= 0.0:
            return
        if verbose:
            _ctx_print_all("Driving right for {} seconds.".format(sec))

    if deg is not None:
        if deg > 360.0:
            _ctx_print_all("Error: The degrees (deg) exceeds 360; will reset to 360.")
            deg = 360.0
        if deg <= 0.0:
            return
        if verbose:
            _ctx_print_all("Driving right for {} degrees.".format(deg))

    motors.drive(-45.0, motors.safe_forward_throttle(), sec, deg)


def pause(sec=1.0, verbose=True):
    """
    Pause the car's code for `sec` seconds.
    """
    if verbose:
        _ctx_print_all("Pausing for {} seconds.".format(sec))
    time.sleep(sec)


def capture(num_frames=1, verbose=True):
    """
    Capture `num_frames` frames from the car's camera and return
    them as a numpy ndarray.
    """
    MAX_FRAMES = 4
    if num_frames > MAX_FRAMES:
        _ctx_print_all(f"Warning: You may capture at most {MAX_FRAMES} frames with this function.")
        num_frames = MAX_FRAMES
    from auto import camera
    return camera.capture(num_frames, verbose)


def plot(frames, also_stream=True, verbose=True):
    """
    Stitch together the given `frames` (a numpy nd-array) into a single nd-array.
    If running in a notebook then the PIL image will be returned (and displayed).
    This function by default also streams the image to your `labs` account.

    The `frames` parameter must be a numpy ndarray with one of the
    following shapes:
        - (n, h, w, 3)   meaning `n` 3-channel RGB images of size `w`x`h`
        - (n, h, w, 1)   meaning `n` 1-channel gray images of size `w`x`h`
        -    (h, w, 3)   meaning a single 3-channel RGB image of size `w`x`h`
        -    (h, w, 1)   meaning a single 1-channel gray image of size `w`x`h`
        -    (h, w)      meaning a single 1-channel gray image of size `w`x`h`
    """
    from auto import frame_streamer
    return frame_streamer.plot(frames, also_stream, verbose)


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
            _ctx_print_all("Instantiated a ColorClassifier object!")

    p1, p2, classific = COLORCLASSIFIER.classify(frame, annotate=annotate)
    if verbose:
        _ctx_print_all("Classified color as '{}'.".format(classific))
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
            _ctx_print_all("Instantiated a FaceDetector object!")

    faces = FACEDETECTOR.detect(frame, annotate=annotate)
    n = len(faces)
    if verbose:
        _ctx_print_all("Found {} face{}.".format(n, 's' if n != 1 else ''))
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
            _ctx_print_all("Instantiated a StopSignDetector object!")

    rects = STOPSIGNDETECTOR.detect(frame, annotate=annotate)
    n = len(rects)
    if verbose:
        _ctx_print_all("Found {} stop sign{}.".format(n, 's' if n != 1 else ''))
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
        if IS_VIRTUAL:
            PEDESTRIANDETECTOR = PedestrianDetector(hitThreshold=-1.5)
        else:
            PEDESTRIANDETECTOR = PedestrianDetector()
        if verbose:
            _ctx_print_all("Instantiated a PedestrianDetector object!")

    rects = PEDESTRIANDETECTOR.detect(frame, annotate=annotate)
    n = len(rects)
    if verbose:
        _ctx_print_all("Found {} pedestrian{}.".format(n, 's' if n != 1 else ''))
    return rects


def object_location(object_list, frame_shape, verbose=True):
    """
    Calculate the location of the largest object in `object_list`.

    Returns one of: 'frame_left', 'frame_right', 'frame_center', None
    """
    if not object_list:
        if verbose:
            _ctx_print_all("Object location is None.")
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
        _ctx_print_all("Object location is '{}'.".format(location))
    return location


def object_size(object_list, frame_shape, verbose=True):
    """
    Calculate the ratio of the nearest object's area to the frame's area.
    """
    if not object_list:
        if verbose:
            _ctx_print_all("Object area is 0.")
        return 0.0
    areas = [w*h for x, y, w, h in object_list]
    ratio = max(areas) / (frame_shape[0] * frame_shape[1])
    if verbose:
        _ctx_print_all("Object area is {}.".format(ratio))
    return ratio


def buzz(notes):
    """
    Play the given `notes` on the device's buzzer.
    """
    from car import buzzer
    buzzer.buzz(notes)


def honk(count=2):
    """
    Make a car horn ("HONK") sound.
    """
    from car import buzzer
    buzzer.honk(count)
