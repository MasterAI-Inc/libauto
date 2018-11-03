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
This module provides many pre-trained and/or pre-configured models which
enable your device to exhibit more advanced behaviors. These models each
provide easy interfaces which abstract the underlying algorithms.
"""

import os
import cv2
import numpy as np


RESOURCE_DIR_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'resources')


class ColorClassifier:
    """
    This class processes images and classifies the color which appears in the
    center region of each image. It classifies the center region as containing
    one of:
      - "red"         <-- the center of the image appears RED
      - "yellow"      <-- the center of the image appears YELLOW
      - "green"       <-- the center of the image appears GREEN
      - "background"  <-- the center of the image appears to be a mix of colors
    """

    # Canonical colors: ordered: red, yellow, green
    DEFAULT_COLORS = np.array([[160,  50, 50],
                               [180, 120,  0],
                               [ 50, 180,  0]])

    DEFAULT_STD_THRESH = np.array([20, 20, 20])

    def __init__(self, center_region_width=0.25,
                       center_region_height=0.25,
                       colors=DEFAULT_COLORS,
                       std_thresh=DEFAULT_STD_THRESH):
        """
        Build a color classifier object which looks at the center region of
        an image and determines if it contains primarily either "red", "yellow",
        or "green", or none of those ("background"). The size of the center
        region is given by the parameters `center_region_width` and
        `center_region_height`.
        """
        self.center_region_width  = center_region_width
        self.center_region_height = center_region_height

        # Colors as canonical vectors [R,G,B]:
        self.colors = colors
        self.color_names = ['red', 'yellow', 'green']

        # Threshold for std deviation cutoff:
        self.std_thresh = std_thresh

    def classify(self, frame, annotate=False, print_debug=False):
        """
        Classify the center region of `frame` as having either primarily "red",
        "yellow", or "green, or none of those ("background").

        The `frame` parameter must be a numpy array containing an RGB image.

        Returns a tuple of the form (`p1`, `p2`, `classific`).
        """

        # Check `frame` for correct shape. It should be an 3-channel, 2d image.
        if len(frame.shape) != 3 or frame.shape[2] != 3:
            raise Exception("incorrect frame shape: Please input an RGB image.")

        # Define the center region of `frame`.
        height, width = frame.shape[0], frame.shape[1]
        y_center      = height/2
        x_center      = width/2
        p1 = int(x_center - (width  * self.center_region_width)/2), \
             int(y_center - (height * self.center_region_height)/2)
        p2 = int(x_center + (width  * self.center_region_width)/2), \
             int(y_center + (height * self.center_region_height)/2)

        # Crop the center region.
        center_frame = frame[ p1[1]:p2[1], p1[0]:p2[0] ]

        # Get mean and std dev values of the pixels in `center_frame`.
        h, w, p = center_frame.shape
        center_reshaped = center_frame.reshape((h*w, p))
        center_mean = np.average(center_reshaped, axis=0).reshape(1, -1)
        center_std = np.std(center_reshaped, axis=0)
        if print_debug:
            print(center_mean)
            print(center_std)

        # Assume the image is just background when all channels have "too big" of
        # standard deviation.
        if (center_std > self.std_thresh).all():
            classific = 'background'

        # Otherwise, find which canonical color is most similar to the center
        # region's mean color.
        else:
            from sklearn.metrics.pairwise import cosine_similarity
            cosine_sims = cosine_similarity(center_mean, self.colors)[0]
            classific = self.color_names[np.argmax(cosine_sims)]

        if annotate:
            self.annotate(p1, p2, classific, frame)

        return p1, p2, classific

    def annotate(self, p1, p2, classific, frame):
        """
        Annotate the image by adding a box around the center region and
        writing the classification on the image to show the result of
        the color classification.
        """
        box_color = None
        text = None
        text_color = None

        if classific == 'green':
            box_color = (0, 255, 0)
            text = 'GREEN'
            text_color = (0, 255, 0)

        elif classific == 'yellow':
            box_color = (255, 255, 0)
            text = 'YELLOW'
            text_color = (0, 0, 0)

        elif classific == 'red':
            box_color = (255, 0, 0)
            text = 'RED'
            text_color = (255, 0, 0)

        elif classific == 'background':
            box_color = (0, 0, 0)
            text = 'background'
            text_color = (0, 0, 0)

        else:
            box_color = (204, 204, 204)

        if box_color:
            cv2.rectangle(frame, p1, p2, box_color, 3)
        if text and text_color:
            cv2.putText(frame, text, p1, cv2.FONT_HERSHEY_SIMPLEX, 1, text_color, 2)


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

