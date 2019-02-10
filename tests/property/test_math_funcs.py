"""Test math functions."""

import hypothesis.strategies as st
import numpy as np
from hypothesis import assume, given

import analysis.math_funcs as mf


@given(
    st.floats(min_value=-1e10, max_value=1e10),
    st.floats(min_value=1e-10, max_value=1e10),
    st.floats(min_value=-1e10, max_value=1e10),
)
def test_gaussian(x, sigma, mu):
    """Test properties of the Gaussian function."""
    mf.gaussian(x, mu=mu) == mf.gaussian(x, mu=mu + 1) - 1

    mf.gaussian(x, sigma=sigma) < mf.gaussian(x, sigma=sigma - 1)
    mf.gaussian(x, sigma=sigma) > mf.gaussian(x, sigma=sigma + 1)


@given(
    st.floats(min_value=0, max_value=1e10),
    st.floats(min_value=1, max_value=50),
)
def test_sigmoid(x, a):
    """Test properties of the sigmoid function."""
    assert mf.sigmoid(x, a) >= mf.sigmoid(x, a - 1)


@given(st.floats(min_value=-500, max_value=500))
def test_sigmoid_range(x):
    """Output of sigmoid function should be in range [-1, 1]."""
    y = mf.sigmoid(x)
    assert y >= -1 and y <= 1


@given(
    st.floats(min_value=0, max_value=1e10),
    st.floats(min_value=0, max_value=1e10))
def test_norm_ratio(a, b):
    """The ratio must be greater than zero and less than or equal to one."""
    assume(a != 0 and b != 0)

    ratio = mf.norm_ratio(a, b)

    assert ratio > 0 and ratio <= 1
    assert np.isclose(ratio * max([a, b]), min([a, b]))
