import numpy as np
import math
from statsmodels import robust


def mad_outliers(x, c):

    mad = robust.mad(x)
    median = np.median(x)

    lower_bound = median - c * mad
    upper_bound = median + c * mad

    x_filtered = np.copy(x)
    x_filtered[np.logical_or(x < lower_bound, x > upper_bound)] = np.nan

    return x_filtered


def sigmoid(x, a=1):

    return 1 / (1 + math.exp(-a * x))


def root_mean_square(x):

    return np.sqrt(sum(x**2) / x.size)


def relative_error(measured, actual, absolute=False):

    error = (measured - actual) / actual

    if absolute:
        error = abs(error)

    return error


def normalize_array(x):
    """
    x : array_like
        Array of length 2 or greater
    """

    max_value = np.nanmax(x)
    min_value = np.nanmin(x)

    return (x - min_value) / (max_value - min_value)


def score_func(measured, actual):

    absolute_error = relative_error(measured, actual, absolute=True)
    normalized_error = sigmoid(absolute_error)

    return math.log(-normalized_error + 1) + 1


def ratio_func(a, b):
    """
    Ratio between two positive inputs.
    If ratio a / b is less than one, the reciprocal is returned instead.

    Parameters
    ----------
    a, b : float
        Positive inputs

    Returns
    -------
    float
        Ratio between a and b
    """
    if a == 0 or b == 0:
        return np.nan

    ratio = np.divide(a, b)

    if ratio < 1:
        ratio = np.reciprocal(ratio)

    return ratio


def matrix_from_labels(expected_values, labels):

    n_rows = len(labels)

    mat = np.full((n_rows, n_rows), np.nan)

    for i, label_i in enumerate(labels):
        for j, label_j in enumerate(labels):

            if label_j in expected_values[label_i]:
                mat[i, j] = expected_values[label_i][label_j]

    return mat


def centre_of_mass(points, masses):

    _, n_dimensions = points.shape

    total = np.zeros(n_dimensions)

    for i, point in enumerate(points):
        mass = masses[i]
        total += mass * point

    centre = total / sum(masses)
    return centre.reshape(-1, 1)


def gaussian(x, mu, sigma):

    coeff = 1.0 / np.sqrt(np.pi * sigma**2)
    exponent = np.exp(- (x - mu)**2 / (2 * sigma**2))

    return coeff * exponent


def pairwise(lst):

    return zip(lst[:-1], lst[1:])
