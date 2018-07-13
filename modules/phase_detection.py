"""Module for detecting the phases of a foot during a walking pass."""

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

import modules.signals as sig
import modules.general as gen
import modules.linear_algebra as lin


def frames_of_interest(foot_signal):
    """
    Return frames of interest from a foot signal.

    These frames are peaks and troughs in the foot signal.

    Parameters
    ----------
    foot_signal : Series
        Signal from foot data that resembles a sinusoid.

    Returns
    -------
    frames_interest : ndarray
        Sorted array of frames.

    """
    signal_1 = sig.normalize(foot_signal)
    signal_2 = 1 - signal_1

    rms_1 = sig.root_mean_square(signal_1)
    rms_2 = sig.root_mean_square(signal_2)

    frames_1 = sig.detect_peaks(signal_1, window_length=3, min_height=rms_1)
    frames_2 = sig.detect_peaks(signal_2, window_length=3, min_height=rms_2)

    frames_interest = np.sort(np.append(frames_1, frames_2))

    return frames_interest


def get_step_signal(foot_series_pass, direction_pass):
    """
    Return a signal that resembles multiple upwards steps.

    This is achieved by representing foot points as 1D values along the
    direction of the walking pass.

    The signal is used to detect the stance and swing phases of the foot.

    Parameters
    ----------
    foot_series_pass : Series
        Positions of a foot during a walking pass.
        Index values are frames.
        Values are foot posit
    direction_pass : ndarray
        Vector for direction of a walking pass.

    Returns
    -------
    step_signal : Series
        Signal with multiple steps.
        Index values are frames.

    """
    line_point = np.array([0, 0, 0])
    points = np.stack(foot_series_pass)

    x_values = lin.line_coordinate_system(line_point, direction_pass, points)

    step_signal = pd.Series(x_values, index=foot_series_pass.index)

    return step_signal


def detect_phases(step_signal, frames_interest):
    """
    Return the phase (stance/swing) of each frame in a walking pass.

    Parameters
    ----------
    step_signal : Series
        Signal with multiple steps.
        Index values are frames.
    frames_interest : ndarray
        Sorted array of frames.

    Returns
    -------
    frame_phases : Series
        Indicates the walking phase of the corresponding frames.
        Each element is either 'stance' or 'swing'.

    """
    frames = step_signal.index.values

    split_labels = gen.label_by_split(frames, frames_interest)
    sub_signals = list(gen.group_by_label(step_signal, split_labels))

    variances = [*map(np.var, sub_signals)]
    variance_array = np.array(variances).reshape(-1, 1)

    k_means = KMeans(n_clusters=2, random_state=0).fit(variance_array)
    variance_labels = k_means.labels_

    sub_signal_lengths = [*map(len, sub_signals)]
    expanded_labels = [*gen.repeat_by_list(variance_labels,
                                           sub_signal_lengths)]

    stance_label = np.argmin(k_means.cluster_centers_)
    swing_label = 1 - stance_label
    phase_dict = {stance_label: 'stance', swing_label: 'swing'}

    phase_strings = gen.map_with_dict(expanded_labels, phase_dict)
    frame_phases = pd.Series(phase_strings, index=frames)

    return frame_phases


def get_phase_dataframe(frame_phases):
    """
    Return a DataFrame displaying the phase and phase number of each frame.

    The phase number is a count of the phase occurence
    (e.g., stance 0, 1, ...).

    Parameters
    ----------
    frame_phases : Series
        Indicates the walking phase of the corresponding frames.
        Each element is either 'stance' or 'swing'.

    Returns
    -------
    df_phase : DataFrame
        Index values are frames.
        Columns are 'Phase', 'Number'.

    """
    frames = frame_phases.index

    df_phase = pd.DataFrame({'Phase': frame_phases},
                            index=frames,
                            dtype='category')

    phase_strings = frame_phases.values
    phase_labels = np.array([*gen.label_repeated_elements(phase_strings)])

    is_stance = df_phase.Phase == 'stance'
    is_swing = df_phase.Phase == 'swing'

    stance_labels = [*gen.label_repeated_elements(phase_labels[is_stance])]
    swing_labels = [*gen.label_repeated_elements(phase_labels[is_swing])]

    stance_series = pd.Series(stance_labels, index=frames[is_stance])
    swing_series = pd.Series(swing_labels, index=frames[is_swing])

    df_phase['Number'] = pd.concat([stance_series, swing_series])
    df_phase.index.name = 'Frame'

    return df_phase
