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
This module provides many pre-trained and/or pre-configured models which
enable your device to exhibit more advanced behaviors. These models each
provide easy interfaces which abstract the underlying algorithms.

This is a **synchronous** interface.
"""

import os
import cv2
import numpy as np
from collections import defaultdict


RESOURCE_DIR_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')


class ColorClassifier:
    """
    This class processes images and classifies the color which appears in the
    center region of each image. It classifies the center region as containing
    one of the RAINBOW or NEUTRAL colors.
    """

    RAINBOW = {
        'red'     : (255,   0,   0),
        'orange'  : (255, 128,   0),
        'yellow'  : (255, 255,   0),
        'green'   : (  0, 255,   0),
        'sky blue': (  0, 255, 255),
        'blue'    : (  0,   0, 255),
        'purple'  : (127,   0, 255),
        'pink'    : (255,   0, 255),
    }
    NEUTRAL = {
        'black'   : (  0,   0,   0),
        'white'   : (255, 255, 255),
    }

    def __init__(self, center_region_width=0.25,
                       center_region_height=0.25,
                       colors={**RAINBOW, **NEUTRAL},
                       min_thresh_to_classify=0.5,
                       ):
        """
        Build a color classifier object which looks at the center region of
        an image and determines if it contains primarily any of the RAINBOW
        or NEUTRAL colors. If the prominent color does not appear in at
        least 10% (min_thresh_to_classify) of the center region then the
        classified color will be 'background'. The size of the center
        region is given by the parameters `center_region_width` and
        `center_region_height`.  If colors is passed in then the keys must
        be a subset of RAINBOW/NEUTRAL.
        """

        self.center_region_width  = center_region_width
        self.center_region_height = center_region_height

        # Colors as canonical vectors [R,G,B]:
        self.colors = colors

        # minimum proportion of pixels in order to classify as color
        self.min_thresh_to_classify = min_thresh_to_classify

        # Cache the color HSV spans.
        self.hsv_span_cache = {color: self._get_hsv_spans(color) for color in self.colors}

    def classify(self, frame, annotate=False, print_debug=False):
        """
        Classify the center region of `frame` as having primarily one of
        the RAINBOW or NEUTRAL colors or 'background'.

        The `frame` parameter must be a numpy array containing an RGB image.

        Returns a tuple of the form (`p1`, `p2`, `color_label).
        """

        # Check `frame` for correct shape. It should be an 3-channel, 2d image.
        if frame.ndim != 3 or frame.shape[2] != 3:
            raise Exception("incorrect frame shape: Please input an RGB image.")

        # Define the center region of `frame`.
        height, width, _ = frame.shape
        y_center         = height/2
        x_center         = width/2
        p1 = int(x_center - (width  * self.center_region_width)/2), \
             int(y_center - (height * self.center_region_height)/2)
        p2 = int(x_center + (width  * self.center_region_width)/2), \
             int(y_center + (height * self.center_region_height)/2)

        # Crop the center region.
        center_frame = frame[ p1[1]:p2[1], p1[0]:p2[0] ]

        color_name = self._get_prominent_color(center_frame)

        if annotate:
            self.annotate(p1, p2, color_name, frame)

        return p1, p2, color_name

    def _get_prominent_color(self, rgb_img):
      """
      Parameters:
          rgb_img (numpy array [shape=(height, width, 3)]):
              image containing 3-channel RGB values

      Returns:
          prominent_color (str):
              name of prominent color

      Convert the image from RGB to the HSV color model. Using
      predefined regions of the HSV model, identify the pixels
      belonging to each color.  The prominent color is the color
      which has the largest proportion of pixels.  If the
      prominent color is less than the min_thresh_to_classify
      then 'background' is the prominent color.
      """
      hsv_img = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2HSV)
      height, width, _ = hsv_img.shape
      pixel_count = height * width
      # dictionary to identify which pixels match a given color {color: pixels}
      bool_pixel_mask = defaultdict(lambda: np.zeros(hsv_img.shape[:2]))
      for color in self.colors:
          for low_hsv, high_hsv in self.hsv_span_cache[color]:
              bool_pixel_mask[color] += (cv2.inRange(hsv_img, low_hsv, high_hsv) == 255)
      proportion = {color: (mask.sum()/pixel_count) for color, mask in bool_pixel_mask.items()}
      prominent_color = max(proportion, key=proportion.get)
      if proportion[prominent_color] < self.min_thresh_to_classify:
          prominent_color = 'background'
      return prominent_color

    def _get_hsv_spans(self, color):
      """
      Parameters:
          color (str):
              name of color

      Returns:
          hsv_spans (list of lists of tuples of ints):
              hsv_spans        : [<hsv_span_1>, <hsv_span_2>]  # only red has more than 1 span
              hsv_span         : [<low_hsv>, <high_hsv>]
              low_hsv/high_hsv : (h,s,v)

      The HSV color model defines a 3d space (cylinder) in which colors are represented.

      Hue:        [ <red>   0 ~ 360 <also red> ] (in the case of cv2: [0 ~ 180])
        The color expressed as an angle on the color wheel, think ROYGBIV-R.
      Saturation: [ <faint> 0 ~ 255 <bold> ]
        The intensity of the color
      Value:      [ <vader> 0 ~ 255 <rice> ]
        The darkness / lightness of the color

      Just as a rectangle can be defined using 2 points, a chunk of the HSV 3d space
      can be identified using 2 HSV values (low, high).  All color variations
      belonging to this chunk (HSV values between low and high) are assigned a
      common color name. This captures deviations in hues, saturations, and values
      for each the common colors.

      Ex:
      green => low_hsv:(42,51,51) ~ high_hsv:(87,255,255)
      """

      SAT_THRESH_WHITE = 40
      # white:   (0 ~ SAT_THRESH_WHITE)
      # rainbow: (SAT_THRESH_WHITE+1 ~ 255)
      VAL_THRESH_BLACK = 50
      # black:   (0 ~ VAL_THRESH_BLACK)
      # rainbow: (VAL_THRESH_BLACK+1 ~ 255)
      HUE_RANGES = {
          'red'     : [(  0,   8),      # lower red
                       (170, 180)],     # upper red
          'orange'  : [(  9,  15)],
          'yellow'  : [( 16,  41)],
          'green'   : [( 42,  87)],
          'sky blue': [( 88,  98)],
          'blue'    : [( 99, 126)],
          'purple'  : [(127, 149)],
          'pink'    : [(150, 169)],
      }
      SAT_RANGES = {
          'black'   :  (  0, 255),
          'white'   :  (  0, SAT_THRESH_WHITE),
          'yellow'  :  (SAT_THRESH_WHITE+20, 255)
      }
      VAL_RANGES = {
          'black'   :  (  0, VAL_THRESH_BLACK),
          'white'   :  (100, 255),   # low end is grey to allow capturing white in low light
      }
      hue_ranges = HUE_RANGES.get(color, [(0, 180)])
      sat_range  = SAT_RANGES.get(color, (SAT_THRESH_WHITE+1, 255))
      val_range  = VAL_RANGES.get(color, (VAL_THRESH_BLACK+1, 255))

      hsv_spans = [list(zip(hue_range, sat_range, val_range)) for hue_range in hue_ranges]
      return hsv_spans

    def annotate(self, p1, p2, color_name, frame):
        """
        Annotate the image by adding a box around the center region and
        writing the color name on the image to show the result of
        the color classification.
        """
        box_color = text_color = self.colors.get(color_name, ColorClassifier.NEUTRAL['black'])
        cv2.rectangle(frame, p1, p2, box_color, 3)
        cv2.putText(frame, color_name.upper(), p1, cv2.FONT_HERSHEY_SIMPLEX, 1, text_color, 2)


class ObjectDetector:
    """
    This is the base-class for all the object detector classes which follow
    in this file.
    Two example sub-classes are `CascadeObjectDetector` and `PedestrianDetector`.
    """

    def __init__(self, box_color, box_line_thickness, text_color,
                       text_str, text_scale, text_line_width):
        """
        Build a object detector object.
        """
        self.box_color = box_color
        self.box_line_thickness = box_line_thickness
        self.text_color = text_color
        self.text_str = text_str
        self.text_scale = text_scale
        self.text_line_width = text_line_width

    def detect(self, frame, annotate=False):
        """
        Detect objects inside of the image `frame`.

        The `frame` parameter must be an image as a numpy array either containing
        3-channel RGB values _or_ 1-channel gray values.

        Returns a list of rectangles, where each rectangle is a 4-tuple of:
            (x, y, width, height)

        This base implementation is abstract and should not be invoked.
        """
        raise Exception("abstract implementation invoked")

    def annotate(self, frame, rectangles):
        """
        Annotate the image by adding boxes and labels around the detected
        objects inside of `frame`. The `rectangles` parameter should be a
        list of 4-tuples where each tuple is:
            (x, y, width, height)
        """
        for x, y, width, height in rectangles:

            cv2.rectangle(frame,
                          (x,          y),
                          (x + width, y + height),
                          self.box_color, self.box_line_thickness)

            cv2.putText(frame, self.text_str, (x, y), cv2.FONT_HERSHEY_SIMPLEX,
                        self.text_scale, self.text_color, self.text_line_width)


class CascadeObjectDetector(ObjectDetector):
    """
    This is the base-class for the _cascade_ object detector classes which follow
    in this file.
    Two example sub-classes are `FaceDetector` and `StopSignDetector`.
    """

    def __init__(self, cascade_file_path,
                       scaleFactor,
                       minNeighbors,
                       minSize,
                       box_color,
                       box_line_thickness,
                       text_color,
                       text_str,
                       text_scale,
                       text_line_width):
        """
        Build a cascade object detector object.
        """
        self.cascade = cv2.CascadeClassifier(cascade_file_path)
        self.scaleFactor = scaleFactor
        self.minNeighbors = minNeighbors
        self.minSize = minSize
        super().__init__(box_color, box_line_thickness, text_color,
                         text_str, text_scale, text_line_width)

    def detect(self, frame, annotate=False):
        """
        Detect objects inside of the image `frame`.

        The `frame` parameter must be an image as a numpy array either containing
        3-channel RGB values _or_ 1-channel gray values.

        Returns a list of rectangles, where each rectangle is a 4-tuple of:
            (x, y, width, height)
        """

        # Get a gray image of the proper shape:
        if frame.ndim == 3:
            if frame.shape[2] == 3:
                frame_gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            elif frame.shape[2] == 1:
                frame_gray = np.squeeze(frame, axis=(2,))
            else:
                raise Exception("invalid number of color channels")
        elif frame.ndim == 2:
            frame_gray = frame
        else:
            raise Exception("invalid frame.ndim")

        # Call the OpenCV cascade.
        rectangles = self.cascade.detectMultiScale(
                frame_gray,
                scaleFactor=self.scaleFactor,
                minNeighbors=self.minNeighbors,
                minSize=self.minSize,
                flags = cv2.CASCADE_SCALE_IMAGE)

        # `rectangles` is a numpy ndarray, but we'd like it to be a list of tuples.
        rectangles = [tuple(rect) for rect in rectangles]

        # Annotate it if the user so desires.
        if annotate:
            self.annotate(frame, rectangles)

        return rectangles


class FaceDetector(CascadeObjectDetector):
    """
    This class detects human faces in images.
    """

    def __init__(self, cascade_file_path=None,
                       scaleFactor=1.1,
                       minNeighbors=3,
                       minSize=(45, 45),
                       box_color=[255, 255, 255],
                       box_line_thickness=3,
                       text_color=[255, 255, 255],
                       text_str='HUMAN',
                       text_scale=1.0,
                       text_line_width=2):
        """
        Build a face detector object.
        """
        if cascade_file_path is None:
            cascade_file_path = os.path.join(RESOURCE_DIR_PATH,
                    "cascades/haarcascade_frontalface_alt.xml")
        super().__init__(cascade_file_path,
                         scaleFactor=scaleFactor,
                         minNeighbors=minNeighbors,
                         minSize=minSize,
                         box_color=box_color,
                         box_line_thickness=box_line_thickness,
                         text_color=text_color,
                         text_str=text_str,
                         text_scale=text_scale,
                         text_line_width=text_line_width)


class StopSignDetector(CascadeObjectDetector):
    """
    This class detects stop signs in images.
    """

    def __init__(self, cascade_file_path=None,
                       scaleFactor=1.1,
                       minNeighbors=10,
                       minSize=(30, 30),
                       box_color=[255, 0, 0],
                       box_line_thickness=3,
                       text_color=[255, 0, 0],
                       text_str='STOP SIGN',
                       text_scale=1.0,
                       text_line_width=2):
        """
        Build a stop sign detector object.
        """
        if cascade_file_path is None:
            cascade_file_path = os.path.join(RESOURCE_DIR_PATH,
                    "cascades/stop_sign.xml")
        super().__init__(cascade_file_path,
                         scaleFactor=scaleFactor,
                         minNeighbors=minNeighbors,
                         minSize=minSize,
                         box_color=box_color,
                         box_line_thickness=box_line_thickness,
                         text_color=text_color,
                         text_str=text_str,
                         text_scale=text_scale,
                         text_line_width=text_line_width)


class PedestrianDetector(ObjectDetector):
    """
    This class detects pedestrians in images.
    """

    def __init__(self, winStride=(4, 4),
                       padding=(8, 8),
                       scale=1.05,
                       box_color=[0, 0, 255],
                       box_line_thickness=3,
                       text_color=[0, 0, 255],
                       text_str='PEDESTRIAN',
                       text_scale=0.75,
                       text_line_width=2):
        """
        Build a pedestrian detector object.
        """
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        self.winStride = winStride
        self.padding = padding
        self.scale = scale
        super().__init__(box_color, box_line_thickness, text_color,
                         text_str, text_scale, text_line_width)

    def detect(self, frame, annotate=False):
        """
        Detect pedestrians inside of the image `frame`.

        The `frame` parameter must be an image as a numpy array either containing
        3-channel RGB values _or_ 1-channel gray values.

        Returns a list of rectangles, where each rectangle is a 4-tuple of:
            (x, y, width, height)
        """

        # Get an RGB image of the proper shape:
        if frame.ndim == 3:
            if frame.shape[2] == 3:
                frame_rgb = frame
            elif frame.shape[2] == 1:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
            else:
                raise Exception("invalid number of color channels")
        elif frame.ndim == 2:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
        else:
            raise Exception("invalid frame.ndim")

        # Call the OpenCV HOG model.
        rectangles, weights = self.hog.detectMultiScale(
                                            frame_rgb,
                                            winStride=self.winStride,
                                            padding=self.padding,
                                            scale=self.scale)

        # `rectangles` is a numpy ndarray, but we'd like it to be a list of tuples.
        rectangles = [tuple(rect) for rect in rectangles]

        # Annotate it if the user so desires.
        if annotate:
            self.annotate(frame, rectangles)

        return rectangles
