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
This module contains demos code for the car-on-track neural network demo.
"""

import numpy as np
import cv2
import os


cv2.setNumThreads(0)

CURR_DIR = os.path.dirname(os.path.realpath(__file__))


def to_gray(img):
    """
    Converts the image `img` from an RGB image to a greyscale image.
    """
    gray_img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    return gray_img


def resize(img):
    """
    Our training set images were captured at a resolution of 160x128, therefore it
    is important that we scale our images here to that size before doing any of the
    other preprocessing. That is what this function does: resize the image `img` to
    be 160x128 pixels.
    """
    width, height = 160, 128
    small_img = cv2.resize(img, (width, height))
    return small_img


def crop(img):
    """
    We only want to keep the bottom 70 rows of pixels of the image.
    We throw away the rows of pixels at the top of the image.
    That's what this function does; it returns only the bottom
    70 rows of pixels from the image `img`.
    """
    height = 70
    return img[-height:, :]


def edges(img):
    """
    This function takes a greyscale image `img` and runs
    the Canny edge detection algorithm on it. The returned
    image will be black and white, where the white parts are
    the edges of the original image `img`.
    """
    canny_thresh_1, canny_thresh_2 = 100, 200
    return cv2.Canny(img, canny_thresh_1, canny_thresh_2)


def preprocess(img):
    """
    This function runs all the functions above, and in the correct order!
    """
    img_edge = edges(resize(to_gray(img)))
    img_feats = crop(np.expand_dims(img_edge, 2))
    img_feats = np.array(img_feats, dtype=np.float32) / 255.0
    return img_edge, img_feats


def load_model():
    """
    Load the pre-trained Neural Network model for the self-driving car.
    """
    print('Importing TensorFlow...')
    from tensorflow.keras.models import load_model as tf_load_model

    print('Loading the Neural Network model...')
    path = os.path.join(CURR_DIR, 'self_drive_model_01.hdf5')
    model = tf_load_model(path)

    return model


def predict(model, img_feats):
    """
    Predict the driving angle from the featurized image.
    """
    samples = np.expand_dims(img_feats, axis=0)   # convert to a batch of length 1
    predictions = model.predict(samples)
    return float(predictions[0][0])

