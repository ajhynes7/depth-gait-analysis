"""Module for statistical calculations."""

from collections import namedtuple

import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error

import analysis.math_funcs as mf


def relative_difference(x, y, absolute=False):
    """
    Relative difference between values x and y.

    Calculated as (x - y) / mean(x, y).

    Parameters
    ----------
    x, y : {int, float, ndarray}
        Input values or arrays.
    absolute : bool, optional
        If True, the absolute relative error is returned
        (the default is False).

    Returns
    -------
    {float, ndarray}
        Relative difference.

    Examples
    --------
    >>> x = np.array([3, 3, 100])
    >>> y = np.array([1, 2, 110])

    >>> np.round(relative_difference(x, y), 3)
    array([ 1.   ,  0.4  , -0.095])

    >>> relative_difference(2, 3)
    -0.4

    >>> relative_difference(2, 3, absolute=True)
    0.4

    """
    difference = x - y
    mean_ = (x + y) / 2

    rel_difference = difference / mean_

    if absolute:
        rel_difference = abs(rel_difference)

    return rel_difference


def relative_error(measured, actual, absolute=False):
    """
    Return the relative errors between measured and actual values.

    Calculated as (measure - actual) / actual.

    Parameters
    ----------
    measured : {int, float, ndarray}
        Measured value or array.

    actual : {int, float, ndarray}
        Actual value or array.

    absolute : bool, optional
        If True, the absolute relative error is returned
        (the default is False).

    Returns
    -------
    error : {float, ndarray}
        Relative error.

    Examples
    --------
    >>> relative_error(2, 5)
    -0.6

    >>> relative_error(3, 5, absolute=True)
    0.4

    >>> x = np.array([1, 2])
    >>> y = np.array([2, 2])
    >>> relative_error(x, y, absolute=True)
    array([0.5, 0. ])

    """
    error = (measured - actual) / actual

    if absolute:
        error = abs(error)

    return error


def bland_altman(differences):
    """
    Calculate measures for Bland-Altman analysis.

    Compare measurements of a new device to those of a validated device.

    Parameters
    ----------
    differences : ndarray
        Differences (relative or absolute) between measurements of two devices.

    Returns
    -------
    BlandAltman : namedtuple
        namedtuple with Bland-Altman parameters.

    Examples
    --------
    >>> measures_1 = np.array([1, 2, 3])
    >>> measures_2 = np.array([2, 2, 3])
    >>> differences = relative_difference(measures_1, measures_2)
    >>> results = bland_altman(differences)

    >>> np.round(results.bias, 2)
    -0.22

    >>> np.round(results.lower_limit, 2)
    -0.84

    >>> np.round(results.upper_limit, 2)
    0.39

    """
    bias, standard_dev = differences.mean(), differences.std()

    lower_limit, upper_limit = mf.limits(bias, 1.96 * standard_dev)

    params = 'bias lower_limit upper_limit range_'

    BlandAltman = namedtuple('BlandAltman', params)

    return BlandAltman(
        bias=bias,
        lower_limit=lower_limit,
        upper_limit=upper_limit,
        range_=upper_limit - lower_limit)


def compare_measurements(df_1, df_2, compare_funcs):
    """
    Compare measurements taken by two devices.

    Parameters
    ----------
    df_1, df_2 : DataFrame
        Measurements of devices 1 and 2.
        Columns are measurement names
        Rows are individual measurements.
    compare_funcs : dict
        Keys are metric names, e.g., relative error
        Values are functions of form column_1, column_2 -> scalar

    Returns
    -------
    df_results : DataFrame
        Columns are measurement names, e.g. stride length
        Rows are metric names, e.g. relative error

    """
    measurements = df_1.columns
    metrics = compare_funcs.keys()

    df_results = pd.DataFrame(index=metrics, columns=measurements)

    for measurement in measurements:
        for metric, func in compare_funcs.items():

            df_results.loc[metric, measurement] = func(df_1[measurement],
                                                       df_2[measurement])

    return df_results


def icc_21(x1, x2):
    """
    Compute intraclass correlation coefficient of type (2, 1) for two raters.

    Measure of absolute agreement between two raters.

    Parameters
    ----------
    x1, x2 : array_like
        Measurements of raters 1 and 2

    Returns
    -------
    float
        ICC(2, 1)

    Examples
    --------
    >>> x1 = [1, 2, 3, 10, 20]
    >>> x2 = [2, 1, 2, 11, 20]

    >>> np.round(icc_21(x1, x2), 3)
    0.974

    >>> np.round(icc_21(x1, [3, 5, 6, 8, 21]), 3)
    0.816

    >>> np.round(icc_21(x1, [3, 5, 6, 5, 2]), 3)
    -0.607

    """
    x_stacked = np.column_stack((x1, x2))
    n, k = x_stacked.shape

    mean_square_rows = np.var(x_stacked, axis=0).mean()
    mean_square_cols = np.var(x_stacked, axis=1).mean()
    mean_square_error = mean_squared_error(x1, x2)

    num = mean_square_rows - mean_square_error
    denom = mean_square_rows + (k - 1) * mean_square_error + k / n * (
        mean_square_cols - mean_square_error)

    return num / denom
