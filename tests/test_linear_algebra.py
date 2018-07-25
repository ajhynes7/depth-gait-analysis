"""Tests for linear algebra module."""

import hypothesis.strategies as st
import numpy as np
import numpy.testing as npt
import pytest
from hypothesis import assume, given

from numpy.linalg import norm

import modules.linear_algebra as lin


floats = st.floats(min_value=-1e10, max_value=1e10)
ints = st.integers(min_value=-1e10, max_value=1e10)

non_zero_vector = st.lists(ints, min_size=2, max_size=5).filter(lambda x:
                                                                any(x))

cross_vector = st.lists(ints, min_size=3, max_size=3).filter(lambda x: any(x))


@given(non_zero_vector, non_zero_vector)
def test_perpendicular(u, v):
    """Two vectors must have an angle of 90 deg if they are perpendicular."""
    assume(len(u) == len(v))

    angle_90 = lin.angle_between(u, v, degrees=True) == 90

    assert lin.is_perpendicular(u, v) == angle_90


@given(cross_vector, cross_vector)
def test_parallel(u, v):
    """If two vectors are parallel, the angle between them must be 0 or 180."""
    angle_uv = lin.angle_between(u, v, degrees=True)

    if lin.is_parallel(u, v):
        angle_0 = np.isclose(angle_uv, 0, atol=1e-5)
        angle_180 = np.isclose(angle_uv, 180)

        assert (angle_0 or angle_180)


@given(non_zero_vector)
def test_unit(vector):
    """
    Tests for converting a vector to a unit vector.

    The unit vector must have a norm of one and the unit operation must be
    idempotent.

    """
    unit_vector = lin.unit(vector)

    assert np.allclose(norm(unit_vector), 1)

    # Unit function is idempotent
    assert np.allclose(unit_vector, lin.unit(unit_vector))


def test_consecutive_dist():

    lengths = [*lin.consecutive_dist(points)]

    npt.assert_array_equal(np.round(lengths, 4), [2.2361, 9.0554, 8.1854])


def test_closest_point():

    target = [2, 3, 4]
    close_point, close_index = lin.closest_point(np.array(points), target)

    assert close_index == 3


def test_project_point_line():

    np.random.seed(0)

    point_a, point_b = np.random.rand(3), np.random.rand(3)
    point_p = np.random.rand(3)

    point_proj = lin.project_point_line(point_p, point_a, point_b)

    vector_ab = point_a - point_b
    vector_proj_p = point_proj - point_p

    dist_proj_line = lin.dist_point_line(point_proj, point_a, point_b)
    dist_p_line = lin.dist_point_line(point_p, point_a, point_b)
    dist_p_proj = norm(point_p - point_proj)

    assert lin.is_perpendicular(vector_ab, vector_proj_p)
    assert lin.is_collinear(point_a, point_b, point_proj)

    assert np.isclose(dist_proj_line, 0)
    assert np.isclose(dist_p_proj, dist_p_line)


def test_project_point_plane():

    np.random.seed(0)

    normal, point_plane = np.random.rand(3), np.random.rand(3)
    point = np.random.rand(3)

    point_proj = lin.project_point_plane(point, point_plane, normal)

    vector_proj_p = point_proj - point

    dist_to_plane = lin.dist_point_plane(point, point_plane, normal)

    assert lin.is_parallel(normal, vector_proj_p)
    assert lin.is_perpendicular(point_plane - point_proj, vector_proj_p)
    assert np.isclose(norm(vector_proj_p), dist_to_plane)


def test_line_distance():

    P = np.array([2, 3, 4])
    A = np.array([1, 5, 4])
    B = np.array([2, 10, 8])

    P_proj = lin.project_point_line(P, A, B)
    d = lin.dist_point_line(P, A, B)

    npt.assert_allclose(d, 1.752549)
    npt.assert_allclose(d, norm(P_proj - P))

    low, high = -10, 10  # Limits for random numbers

    for _ in range(10):

        dim = np.random.randint(2, 3)  # Vector dimension

        # Generate random arrays
        P, A, B = [np.random.uniform(low, high, dim)
                   for _ in range(3)]

        P_proj = lin.project_point_line(P, A, B)
        d = lin.dist_point_line(P, A, B)

        npt.assert_allclose(d, norm(P_proj - P))


def test_plane_distance():

    low, high = -10, 10

    for _ in range(10):

        dim = np.random.randint(1, 5)  # Vector dimension

        # Generate random arrays
        P, P_plane, normal = [np.random.uniform(low, high, dim)
                              for _ in range(3)]

        P_proj = lin.project_point_plane(P, P_plane, normal)
        d = lin.dist_point_plane(P, P_plane, normal)

        npt.assert_allclose(d, norm(P_proj - P))


@pytest.mark.parametrize("test_input, expected", [
    (np.array([1, 1, 0]), 'straight'),
    (np.array([-1, 5, 0]), 'straight'),
    (np.array([0, 5, 1]), 'left'),
    (np.array([0, -5, -10]), 'right'),
    (np.array([4, 2, 1]), 'left'),
])
def test_target_side(test_input, expected):

    forward = np.array([1, 0, 0])
    up = np.array([0, 1, 0])

    assert lin.target_side(test_input, forward, up) == expected


def test_best_fit_line_1():

    points = np.random.rand(10, 3)
    _, direction = lin.best_fit_line(points)

    points_reversed = np.flip(points, axis=0)

    _, direction_reversed = lin.best_fit_line(points_reversed)

    # The two vectors should be parallel
    cross_prod = np.cross(direction_reversed, direction)
    npt.assert_array_almost_equal(cross_prod, np.array([0, 0, 0]))

    npt.assert_allclose(norm(direction), 1)


@pytest.mark.parametrize("points, centroid, direction", [
    (np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0]]), np.array([1, 0, 0]),
     np.array([1, 0, 0])),
    (np.array([[0, 0], [4, 0]]), np.array([2, 0]), np.array([1, 0])),
    (np.array([[0, 0], [0, -10]]), np.array([0, -5]), np.array([0, -1])),
])
def test_best_fit_line_2(points, centroid, direction):

    centroid_calc, direction_calc = lin.best_fit_line(points)

    npt.assert_allclose(centroid, np.round(centroid_calc, 2))
    npt.assert_allclose(direction, direction_calc)


@pytest.mark.parametrize("points, centroid, normal", [
    (np.array([[0, 0, 0], [1, 0, 0], [0, 0, 1]]), np.array([0.33, 0, 0.33]),
     np.array([0, -1, 0])),
    (np.array([[0, 0, 0], [3, 0, 0], [0, 3, 0]]), np.array([1, 1, 0]),
     np.array([0, 0, 1])),
])
def test_best_fit_plane(points, centroid, normal):

    centroid_calc, normal_calc = lin.best_fit_plane(points)

    npt.assert_allclose(centroid, np.round(centroid_calc, 2))
    npt.assert_allclose(normal, normal_calc)


@pytest.mark.parametrize("a, b, expected", [
    (np.array([2, 0]), np.array([-2, 0]), np.pi),
    (np.array([5, 5, 5]), np.array([1, 1, 1]), 0),
    (np.array([1, 0]), np.array([1, 1]), np.pi / 4),
    (np.array([1, 0]), np.array([-5, -5]), 3 * np.pi / 4),
])
def test_angle_between(a, b, expected):

    angle = lin.angle_between(a, b)

    npt.assert_allclose(angle, expected)


def test_for_failure():
    """
    Test that functions fail when floating-point errors occur,
    such as division by zero.

    """
    P = np.array([1, 2])
    A, B = np.array([5, 5]), np.array([5, 5])

    with pytest.raises(Exception):

        lin.unit(np.zeros(3))

        lin.dist_point_line(P, A, B)

        lin.project_point_line(P, A, B)

        lin.angle_between(A, B)


points = [[1, 2, 3], [2, 2, 5], [-1, 10, 2], [2, 3, 5]]
