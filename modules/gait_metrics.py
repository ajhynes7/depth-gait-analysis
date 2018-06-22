import numpy as np
import pandas as pd
from numpy.linalg import norm

import modules.general as gen
import modules.linear_algebra as lin
import modules.clustering as cl
import modules.math_funcs as mf


class FootMetrics:

    def __init__(self, stance_feet, swing_feet, frames):

        self.stance_i, self.stance_f = stance_feet
        self.swing_i, self.swing_f = swing_feet

        self.frame_i, self.frame_f = frames

        self.stance = (self.stance_i + self.stance_f) / 2

        self.stance_proj = lin.proj_point_line(self.stance, self.swing_i,
                                               self.swing_f)

    def __str__(self):

        string = "FootMetrics(frame_i={self.frame_i}, frame_f={self.frame_f})"

        return string.format(self=self)

    @property
    def stride_length(self):

        return norm(self.swing_f - self.swing_i)

    @property
    def step_length(self):

        return norm(self.stance_proj - self.swing_i)

    @property
    def stride_width(self):

        return norm(self.stance_proj - self.stance)

    @property
    def absolute_step_length(self):

        return norm(self.stance - self.swing_i)


class HeadMetrics:

    def __init__(self, head_points, frames):

        self.head_i, self.head_f = head_points

        self.frame_i, self.frame_f = frames

    def __str__(self):

        string = "HeadMetrics(frame_i={self.frame_i}, frame_f={self.frame_f})"

        return string.format(self=self)

    @property
    def stride_time(self):

        return (self.frame_f - self.frame_i) / 30

    @property
    def stride_velocity(self):

        d_head = norm(self.head_f - self.head_i)

        return d_head / self.stride_time


def foot_dist_peaks(foot_dist, r=1):
    """
    Find peaks in the foot distance data.

    Applies mean shift to the foot distance values
    greater than the root mean square.

    Parameters
    ----------
    foot_dist : pandas Series
        Distance between feet at each frame.
        Index values are frame numbers.
    r : {int, float}, optional
        Radius for mean shift clustering (default is 1).

    Returns
    -------
    peak_frames : ndarray
        Frames where foot distance is at a peak.
    mid_frames : ndarray
        Frames closest to cluster centroids.

    """
    frames = foot_dist.index.values

    # Upper foot distance values are those above
    # the root mean square value
    rms = mf.root_mean_square(foot_dist.values)
    is_upper_value = foot_dist > rms

    # Find centres of foot distance peaks with mean shift
    upper_frames = frames[is_upper_value].reshape(-1, 1)
    labels, centroids, k = cl.MeanShift.cluster(upper_frames,
                                                kernel='gaussian', radius=r)

    # Find frames with highest foot distance in each mean shift cluster
    upper_foot_dist = foot_dist[is_upper_value]
    peak_frames = [upper_foot_dist[labels == label].idxmax() for label in
                   range(k)]

    # Find the frames closest to the mean shift centroids
    mid_frames = [lin.closest_point(upper_frames, x)[0].item()
                  for x in centroids]

    return np.unique(peak_frames), np.unique(mid_frames),


def assign_swing_stance(foot_points_i, foot_points_f):
    """
    Assign initial and final foot points to the stance and swing foot.

    Returns the combination that minimizes
    the distance travelled by the stance foot.

    Parameters
    ----------
    foot_points_i : ndarray
        The two initial foot points (at start of stride).
    foot_points_f : ndarray
        The two final foot points (at end of stride).

    Returns
    -------
    points_i : ndarray
        Initial foot points in order of (stance, swing).
    points_f : ndarray
        Final foot points in order of (stance, swing).

    """
    min_dist = np.inf
    points_i, points_f = [], []

    for a in range(2):
        for b in range(2):

            stance_i = foot_points_i[a, :]
            stance_f = foot_points_f[b, :]

            swing_i = foot_points_i[1 - a, :]
            swing_f = foot_points_f[1 - b, :]

            d_stance = norm(stance_f - stance_i)

            if d_stance < min_dist:

                min_dist = d_stance

                points_i = np.array([stance_i, swing_i])
                points_f = np.array([stance_f, swing_f])

    return points_i, points_f


def foot_metrics(df, frame_i, frame_f):

    foot_points_i = np.stack(df.loc[frame_i, ['L_FOOT', 'R_FOOT']])
    foot_points_f = np.stack(df.loc[frame_f, ['L_FOOT', 'R_FOOT']])

    points_i, points_f = assign_swing_stance(foot_points_i, foot_points_f)

    stance_i, swing_i = points_i
    stance_f, swing_f = points_f

    stance_feet = stance_i, stance_f
    swing_feet = swing_i, swing_f
    frames = frame_i, frame_f

    foot_obj = FootMetrics(stance_feet, swing_feet, frames)

    return gen.get_properties(FootMetrics, foot_obj)


def head_metrics(df, frame_i, frame_f):

    head_points = df.HEAD[[frame_i, frame_f]]

    frames = frame_i, frame_f

    head_obj = HeadMetrics(head_points, frames)

    return gen.get_properties(HeadMetrics, head_obj)


def gait_dataframe(df, peak_frames, peak_labels):
    """
    Produces a pandas DataFrame containing gait metrics from a walking trial.

    Parameters
    ----------
    df : DataFrame
        Index is the frame numbers.
        Columns include 'HEAD', 'L_FOOT', 'R_FOOT'.
        Each element is a position vector.
    peak_frames : array_like
        Array of all frames with a detected peak in the foot distance data.
    peak_labels : dict
        Label of each peak frame.
        The labels are determined by clustering the peak frames.

    Returns
    -------
    gait_df : DataFrame
        Index is final peak frame used to calculate gait metrics.
        Columns are gait metric names.

    """
    gait_list, frame_list = [], []

    for frame_i, frame_f in gen.pairwise(peak_frames):

        if peak_labels[frame_i] == peak_labels[frame_f]:

            foot_measures = foot_metrics(df, frame_i, frame_f)
            head_measures = head_metrics(df, frame_i, frame_f)

            metrics = {**foot_measures, **head_measures}

            gait_list.append(metrics)
            frame_list.append(frame_f)

    gait_df = pd.DataFrame(gait_list, index=frame_list)
    gait_df.index.name = 'Frame'

    return gait_df
