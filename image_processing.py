import numpy as np
from skimage.exposure import *


def cvt_to_float(matrix):
    return matrix / matrix.max()


def get_histogram_clipped_min_max(matrix, lowclip, highclip, bitness=16):
    data_max_value = 2 ** bitness
    hist, bins = np.histogram(matrix.ravel(), data_max_value, [0, data_max_value])
    cdf = np.cumsum(hist)
    cdfmax = cdf.max()
    min_value = cdf[(cdf >= lowclip * cdfmax)][0]
    min_pixel_value = np.where(cdf == min_value)
    max_value = cdf[(cdf >= (cdfmax - (highclip * cdfmax)))]
    max_pixel_value = np.where(cdf == max_value)
    return min_pixel_value, max_pixel_value


def linear_rescale(matrix, min_value: float = 0, max_value: float = 1):
    matrix = matrix - min_value
    matrix = matrix * 255.0
    matrix = matrix / (max_value - min_value)
    return matrix


def clahe_rescale(matrix):
    matrix = matrix / matrix.max()
    matrix = equalize_adapthist(matrix)
    matrix = matrix * 255.0
    return matrix
