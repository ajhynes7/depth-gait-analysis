from collections import namedtuple

import numpy as np
import pandas as pd
from numpy.linalg import norm

import modules.general as gen
import modules.linear_algebra as lin
import modules.clustering as cl
import modules.math_funcs as mf


class Stride():

    def __init__(self, state_i, state_f):

        self.stance_i = state_i.stance
        self.stance_f = state_f.stance

        self.swing_i = state_i.swing
        self.swing_f = state_f.swing

        self.frame_i = state_i.frame
        self.frame_f = state_f.frame

        self.stance = (self.stance_i + self.stance_f) / 2

        self.proj_stance = lin.proj_point_line(self.stance, self.swing_i,
                                               self.swing_f)

    def __str__(self):

        string = "Stride(frame_i={self.frame_i}, frame_f={self.frame_f})"

        return string.format(self=self)

    @property
    def stride_length(self):
        return norm(self.swing_f - self.swing_i)

    @property
    def step_length(self):

        return norm(self.proj_stance - self.swing_i)

    @property
    def stride_width(self):
        return norm(self.proj_stance - self.stance)

    @property
    def absolute_step_length(self):

        return norm(self.stance - self.swing_i)

    @property
    def stride_time(self):

        return (self.frame_f - self.frame_i) / 30

    @property
    def stride_velocity(self):

        return self.stride_length / self.stride_time


def foot_dist_peaks(foot_dist, frame_labels, r=1):
    """
    [description]

    Parameters
    ----------
    foot_dist : {[type]}
        [description]
    frame_labels : {[type]}
        [description]
    r : {number}, optional
        [description] (the default is 1, which [default_description])

    Returns
    -------
    [type]
        [description]
    """

    frames = foot_dist.index.values.reshape(-1, 1)

    # Upper foot distance values are those above
    # the root mean square value
    rms = mf.root_mean_square(foot_dist.values)
    is_upper_value = foot_dist > rms

    n_labels = frame_labels.max() + 1
    frame_list = []

    # Each label represent one walking pass by the camera
    for i in range(n_labels):

        # Upper foot distance values of one walking pass
        upper_of_pass = (frame_labels == i) & is_upper_value

        # Find centres of foot distance peaks with mean shift
        input_frames = frames[upper_of_pass]
        _, centroids, k = cl.mean_shift(input_frames,
                                        cl.gaussian_kernel_shift, radius=r)

        # Find the frames closest to the mean shift centroids
        upper_pass_frames = frames[upper_of_pass]
        centroid_frames = [lin.closest_point(upper_pass_frames,
                                             x)[0].item() for x in centroids]

        frame_list.append(centroid_frames)

    # Flatten list and sort to obtain peak frames from whole walking trial
    peak_frames = sorted([x for sublist in frame_list for x in sublist])

    # Duplicate frames may have occurred from finding the frames closest
    # to the cluster centroids
    return np.unique(peak_frames)


def assign_swing_stance(foot_points_i, foot_points_f):
    """
    [description]

    Parameters
    ----------
    foot_points_i : {[type]}
        [description]
    foot_points_f : {[type]}
        [description]

    Returns
    -------
    [type]
        [description]
    """

    max_range = 0

    for a in range(2):
        for b in range(2):

            P_stance_i = foot_points_i[a, :]
            P_stance_f = foot_points_f[b, :]

            P_swing_i = foot_points_i[1 - a, :]
            P_swing_f = foot_points_f[1 - b, :]

            d_stance = norm(P_stance_f - P_stance_i)
            d_swing = norm(P_swing_f - P_swing_i)

            d_range = d_swing - d_stance

            if d_range > max_range:

                max_range = d_range

                points_i = np.array([P_stance_i, P_swing_i])
                points_f = np.array([P_stance_f, P_swing_f])

    return points_i, points_f


def get_gait_metrics(df, frame_i, frame_f):
    """
    Uses two consecutive peak frames to calculate gait metrics.
    The peak frames are from the foot-to-foot distance data.
    Two consecutive peaks indicate a full walking stride.

    Parameters
    ----------
    df : pandas DataFrame.
        | Index is the frame numbers.
        | Columns include 'HEAD', 'L_FOOT', 'R_FOOT'.
        | Each element is a position vector.
    frame_i : int
        Initial peak frame.
    frame_f : int
        Final peak frame.

    Returns
    -------
    metrics : dict
        Gait metrics.

    """
    foot_points_i = np.stack(df.loc[frame_i, ['L_FOOT', 'R_FOOT']])
    foot_points_f = np.stack(df.loc[frame_f, ['L_FOOT', 'R_FOOT']])

    points_i, points_f = assign_swing_stance(foot_points_i, foot_points_f)

    stance_i, swing_i = points_i
    stance_f, swing_f = points_f

    State = namedtuple('State', 'frame, stance, swing')
    state_i = State(frame_i, stance_i, swing_i)
    state_f = State(frame_f, stance_f, swing_f)

    stride_obj = Stride(state_i, state_f)

    metrics = {}

    for x in vars(Stride):

        if isinstance(getattr(Stride, x), property):

            metrics[x] = getattr(stride_obj, x)

    return metrics


def gait_dataframe(df, peak_frames, peak_labels):
    """
    Produces a pandas DataFrame containing gait metrics from a walking trial.

    Parameters
    ----------
    df : DataFrame
        | Index is the frame numbers
        | Columns include 'HEAD', 'L_FOOT', 'R_FOOT'
        | Each element is a position vector
    peak_frames : array_like
        Array of all frames with a detected peak in the foot distance data
    peak_labels : dict
        | Label of each peak frame
        | The labels are determined by clustering the peak frames

    Returns
    -------
    gait_df : DataFrame
        | Index is final peak frame used to calculate gait metrics
        | Columns are gait metric names
    """
    gait_list, frame_list = [], []

    for frame_i, frame_f in gen.pairwise(peak_frames):

        if peak_labels[frame_i] == peak_labels[frame_f]:

            metrics = get_gait_metrics(df, frame_i, frame_f)

            gait_list.append(metrics)
            frame_list.append(frame_f)

    gait_df = pd.DataFrame(gait_list, index=frame_list)
    gait_df.index.name = 'Frame'

    return gait_df
