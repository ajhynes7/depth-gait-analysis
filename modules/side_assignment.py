"""Module for assigning left/right sides to the feet."""

from collections import namedtuple

import numpy as np
from dpcontracts import require, ensure
from skimage.measure import LineModelND, ransac
from skspatial.objects import Vector
from statsmodels.robust import mad

import modules.numpy_funcs as nf


@require("The input points must be 3D.", lambda args: args.points.shape[1] == 3)
@ensure("The output points must be 2D.", lambda _, result: result.shape[1] == 2)
def reduce_dimension(points):

    return np.column_stack((points[:, 0], points[:, 2]))


def fit_ransac(points):
    """Fit a line to 3D points with RANSAC."""

    model, is_inlier = ransac(
        points, LineModelND, min_samples=int(0.5 * len(points)), residual_threshold=2.5 * min(mad(points))
    )

    return model, is_inlier


def compute_basis(frames, points_a, points_b):
    """Return origin and basis vectors of new coordinate system found with RANSAC."""

    frames_grouped = np.repeat(frames, 2)
    points_grouped = nf.interweave_rows(points_a, points_b)

    points_grouped_2d = reduce_dimension(points_grouped)

    model_ransac, is_inlier = fit_ransac(points_grouped_2d)
    point_origin, vector_forward = model_ransac.params

    vector_up = [0, 0, 1]
    vector_perp = Vector(vector_forward).cross(vector_up)[:-1]

    frames_grouped_inlier = frames_grouped[is_inlier]
    points_grouped_inlier = points_grouped_2d[is_inlier]

    Basis = namedtuple('Basis', 'origin, forward, up, perp')
    basis = Basis(point_origin, vector_forward, vector_up, vector_perp)

    return basis, frames_grouped_inlier, points_grouped_inlier


def assign_sides_grouped(frames_grouped, values_side_grouped, labels_grouped):

    labels_unique = np.unique(labels_grouped[labels_grouped != -1])
    set_labels_r = set()

    for label in labels_unique:

        is_cluster = labels_grouped == label

        # Element is True for all cluster frames in the grouped array.
        is_frame_cluster = np.in1d(frames_grouped, frames_grouped[is_cluster])

        # Element is True if the corresponding foot point occurred on a frame in the cluster,
        # but is not a part of the cluster itself. This means it is a swing foot.
        is_foot_swing = is_frame_cluster & ~is_cluster

        value_side_stance = np.median(values_side_grouped[is_cluster])

        if is_foot_swing.sum() > 0:
            value_side_swing = np.median(values_side_grouped[is_foot_swing])
        else:
            # It's possible that there are no swing feet in the cluster.
            # In this case, the swing value is assumed to be zero.
            value_side_swing = 0

        if value_side_stance > value_side_swing:
            # The current label is on the right side.
            set_labels_r.add(label)

    set_labels_l = set(labels_unique) - set_labels_r

    is_label_grouped_l = np.in1d(labels_grouped, list(set_labels_l))
    is_label_grouped_r = np.in1d(labels_grouped, list(set_labels_r))

    labels_grouped_l = np.copy(labels_grouped)
    labels_grouped_r = np.copy(labels_grouped)

    labels_grouped_l[~is_label_grouped_l] = -1
    labels_grouped_r[~is_label_grouped_r] = -1

    return labels_grouped_l, labels_grouped_r
