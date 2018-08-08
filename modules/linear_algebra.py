"""Operations dealing with linear algebra, such as projection and distances."""

import numpy as np
from numpy.linalg import norm


def unit(v, **kwargs):
    """
    Return the unit vector of v.

    Parameters
    ----------
    v : array_like
        Input vector.
    kwargs : dict, optional
        Additional keywords passed to `np.isclose`.

    Returns
    -------
    ndarray
        Unit vector.

    Raises
    ------
    ValueError
        When the vector norm is zero.

    Examples
    --------
    >>> unit([5, 0, 0])
    array([1., 0., 0.])

    >>> unit([0, -2])
    array([ 0., -1.])

    >>> unit([0, 0])
    Traceback (most recent call last):
    ValueError: The vector norm is zero.

    """
    length = norm(v)

    if np.isclose(length, 0, **kwargs):
        raise ValueError("The vector norm is zero.")

    return v / length


def is_perpendicular(u, v, **kwargs):
    """
    Check if two vectors are perpendicular.

    The vectors are perpendicular if their dot product is zero.

    Parameters
    ----------
    u, v : array_like
        Input vectors
    kwargs : dict, optional
        Additional keywords passed to `np.isclose`.

    Returns
    -------
    bool
        True if vectors are perpendicular.

    Examples
    --------
    >>> is_perpendicular([0, 1], [1, 0])
    True

    >>> is_perpendicular([-1, 5], [3, 4])
    False

    >>> is_perpendicular([2, 0, 0], [0, 0, 2])
    True

    The zero vector is perpendicular to all vectors.

    >>> is_perpendicular([0, 0, 0], [1, 2, 3])
    True

    """
    return np.isclose(np.dot(u, v), 0, **kwargs)


def is_parallel(u, v, **kwargs):
    """
    Check if two vectors are parallel.

    Parameters
    ----------
    u, v : array_like
        Input vectors
    kwargs : dict, optional
        Additional keywords passed to `np.allclose`.

    Returns
    -------
    bool
        True if vectors are parallel.

    Examples
    --------
    >>> is_parallel([0, 1], [1, 0])
    False

    >>> is_parallel([-1, 5], [2, -10])
    True

    >>> is_parallel([1, 2, 3], [3, 6, 9])
    True

    """
    return np.allclose(np.cross(u, v), 0, **kwargs)


def is_collinear(point_a, point_b, point_c, **kwargs):
    """
    Check if three points are collinear.

    Points A, B, C are collinear if AB is parallel to AC.

    Parameters
    ----------
    point_a, point_b, point_c : ndarray
        Input points.
    kwargs : dict, optional
        Additional keywords passed to `np.allclose`.

    Returns
    -------
    bool
        True if points are collinear.

    Examples
    --------
    >>> is_collinear([0, 1], [1, 0], [1, 2])
    False

    >>> is_collinear([1, 1], [2, 2], [5, 5])
    True

    """
    vector_ab = np.subtract(point_a, point_b)
    vector_ac = np.subtract(point_a, point_c)

    return is_parallel(vector_ab, vector_ac, **kwargs)


def project_point_line(point_p, line_point_a, line_point_b):
    """
    Project a point onto a line.

    Parameters
    ----------
    point_p : ndarray
        Point P in space.
    line_point_a : ndarray
        Point A on line.
    line_point_b : ndarray
        Point B on line.

    Returns
    -------
    ndarray
        Projection of point P onto the line.

    Raises
    ------
    ValueError
        When the distance between line points A and B is zero.

    Examples
    --------
    >>> line_point_a, line_point_b = np.array([0, 0]), np.array([1, 0])

    >>> project_point_line(np.array([0, 5]), line_point_a, line_point_b)
    array([0., 0.])

    >>> line_point_a, line_point_b = np.array([1, 1]), np.array([1, 1])
    >>> project_point_line(np.array([0, 5]), line_point_a, line_point_b)
    Traceback (most recent call last):
    ValueError: Division by zero.

    """
    vec_ap = point_p - line_point_a  # Vector from A to P
    vec_ab = line_point_b - line_point_a  # Vector from A to B

    num = np.dot(vec_ap, vec_ab)
    denom = np.dot(vec_ab, vec_ab)

    if denom == 0:
        raise ValueError("Division by zero.")

    coeff = num / denom

    # Project point onto line
    return line_point_a + coeff * vec_ab


def project_point_plane(point, point_plane, normal):
    """
    Project a point onto a plane.

    Parameters
    ----------
    point : ndarray
        Point in space.
    point_plane : ndarray
        Point on plane.
    normal : ndarray
        Normal vector of plane.

    Returns
    -------
    ndarray
        Projection of point P onto the plane..

    Examples
    --------
    >>> point_plane, normal = np.array([0, 0, 0]), np.array([0, 0, 1])

    >>> project_point_plane(np.array([10, 2, 5]), point_plane, normal)
    array([10.,  2.,  0.])

    """
    unit_normal = unit(normal)

    return point - np.dot(point - point_plane, unit_normal) * unit_normal


def best_fit_line(points):
    """
    Return the line of best fit for a set of points.

    The direction of the line depends on the order of the points.

    Parameters
    ----------
    points : ndarray
         (n, d) array of n points with dimension d.

    Returns
    -------
    centroid : ndarray
        Centroid of points. Line of best fit passes through centroid.
    direction : ndarray
        Unit direction vector for line of best fit.
        Right singular vector which corresponds to the largest
        singular value of A.

    Raises
    ------
    ValueError
        When fewer than two points are input (line would be underdefined).

    Examples
    --------
    >>> points = np.array([[1, 0], [2, 0], [3, 0]])
    >>> centroid, direction = best_fit_line(points)

    >>> centroid
    array([2., 0.])

    >>> direction
    array([1., 0.])

    >>> _, direction = best_fit_line(np.flip(points, axis=0))
    >>> direction.astype(int)
    array([-1,  0])

    """
    n_points, _ = points.shape
    if n_points < 2:
        raise ValueError('At least two points required.')

    # Ensure that points have no nan values
    points = points[~np.isnan(points).any(axis=1)]

    centroid = np.mean(points, axis=0)

    _, _, vh = np.linalg.svd(points - centroid)

    direction = vh[0, :]

    return centroid, direction


def target_side_value(forward, up, target):
    """
    Return a signed value indicating the left/right direction of a target.

    The orientation is defined by specifying the forward and up directions.

    Parameters
    ----------
    forward : array_like
        Vector for forward direction.
    up : array_like
        Vector for up direction.
    target : array_like
        Vector for up direction.

    Returns
    -------
    float
        Signed value indicating left/right direction of a target.
        A positive value indicates right, while negative indicates left.
        The magnitude of the value is greater when the target is further to
        the left/right.

    Examples
    --------
    >>> forward, up = [0, 1, 0], [0, 0, 1]

    >>> target_side_value(forward, up, [1, 10, 0])
    1.0

    >>> target_side_value([0, -1, 0], up, [1, 10, 0])
    -1.0

    The magnitude of the forward and up vectors does not affect the value.
    >>> target_side_value([0, 5, 0], [0, 0, 3], [1, 10, 0])
    1.0

    >>> target_side_value(forward, up, [3, 10, 0])
    3.0

    >>> target_side_value(forward, up, [-4, 5, 5])
    -4.0

    """
    normal = unit(np.cross(forward, up))

    return np.dot(normal, target)


def angle_between(u, v, degrees=False):
    """
    Compute the angle between vectors u and v.

    Parameters
    ----------
    u, v : array_like
        Input vectors

    degrees : bool, optional
        Set to true for angle in degrees rather than radians.

    Returns
    -------
    theta : float
        Angle between vectors.

    Examples
    --------
    >>> angle_between([1, 0], [1, 0])
    0.0

    >>> u, v = [1, 0], [1, 1]
    >>> round(angle_between(u, v, degrees=True))
    45.0

    >>> u, v = [1, 0], [-2, 0]
    >>> round(angle_between(u, v, degrees=True))
    180.0

    >>> u, v = [1, 1, 1], [1, 1, 1]
    >>> angle_between(u, v)
    0.0

    """
    cos_theta = np.dot(unit(u), unit(v))

    # The allowed domain for arccos is [-1, 1]
    if cos_theta > 1:
        cos_theta = 1
    elif cos_theta < -1:
        cos_theta = -1

    theta = np.arccos(cos_theta)

    if degrees:
        theta = np.rad2deg(theta)

    return theta


def line_coordinate_system(line_point, direction, points):
    """
    Represent points in a one-dimensional coordinate system defined by a line.

    The input line point acts as the origin of the coordinate system.

    The line is analagous to an x-axis. The output coordinates represent the
    x-values of points on this line.

    Parameters
    ----------
    line_point : ndarray
        Point on line.
    direction : ndarray
        Direction vector of line.
    points : ndarray
        (n, d) array of n points with dimension d.

    Returns
    -------
    coordinates : ndarray
        One-dimensional coordinates.

    Examples
    --------
    >>> line_point = np.array([0, 0])
    >>> direction = np.array([1, 0])

    >>> points = np.array([[10, 2], [3, 4], [-5, 5]])

    >>> line_coordinate_system(line_point, direction, points)
    array([10,  3, -5])

    """
    vectors = points - line_point

    coordinates = np.apply_along_axis(np.dot, 1, vectors, direction)

    return coordinates
