"""Module for detecting the phases of a foot during a walking pass."""

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

import modules.iterable_funcs as itf
import modules.linear_algebra as lin
import modules.numpy_funcs as nf
import modules.pandas_funcs as pf
import modules.sliding_window as sw


def detect_phases(frames, step_signal):
    """
    Detect the stance/swing phases of a foot during a walking pass.

    Parameters
    ----------
    frames : ndarray
        (n, ) array of frame numbers.
    step_signal : ndarray
        (n, ) array of values indicating the motion of one foot.

    Returns
    -------
    is_stance : ndarray
        (n, ) array of boolean values.
        Element is True if the corresponding foot is in the stance phase.

    """
    frames_exp, step_signal_exp = nf.expand_arrays(frames, step_signal)

    pad_width = 5
    cluster_values = sw.apply_to_padded(step_signal_exp, np.nanvar, pad_width,
                                        'reflect', reflect_type='odd')

    points = nf.to_column(cluster_values)
    k_means = KMeans(n_clusters=2, random_state=0).fit(points)

    stance_label = np.argmin(k_means.cluster_centers_)
    is_stance_exp = k_means.labels_ == stance_label

    # Collapse vector to original length of the frames list.
    is_stance = is_stance_exp[~np.isnan(step_signal_exp)]

    # Remove small groups of consecutive stance frames, because these could
    # be false positives.
    is_stance = nf.filter_consecutive_true(is_stance, min_length=10)

    return is_stance


def get_phase_dataframe(foot_series, direction_pass):
    """
    Return a DataFrame displaying the phase and phase number of each frame.

    The phase number is a count of the phase occurrence.
    (e.g., stance 0, 1, ...).

    Parameters
    ----------
    foot_series : ndarray
        Index is 'frame'.
        Values are foot positions.
    direction_pass : ndarray
        Direction of motion for the walking pass.

    Returns
    -------
    df_phase : DataFrame
        Index is 'frame'.
        Columns are 'phase', 'position', 'number'.

    """
    frames = foot_series.index.values
    foot_points = np.stack(foot_series)

    step_signal = lin.line_coordinate_system(np.zeros(3), direction_pass,
                                             foot_points)

    is_stance = detect_phases(frames, step_signal)

    is_stance_series = pd.Series(is_stance, index=frames)
    is_stance_series.replace({True: 'stance', False: 'swing'}, inplace=True)

    df_phase = pd.DataFrame({'phase': is_stance_series}, dtype='category')
    df_phase['position'] = foot_series

    # Unique label for each distinct phase in the walking pass.
    # e.g. swing, stance, swing section get labelled 0, 1, 2.
    phase_labels = np.array([*itf.label_repeated_elements(is_stance)])

    is_swing = ~is_stance

    # Count of each phase in the walking pass.
    stance_numbers = [*itf.label_repeated_elements(phase_labels[is_stance])]
    swing_numbers = [*itf.label_repeated_elements(phase_labels[is_swing])]

    stance_series = pd.Series(stance_numbers, index=frames[is_stance])
    swing_series = pd.Series(swing_numbers, index=frames[is_swing])
    df_phase['number'] = pd.concat([stance_series, swing_series])

    df_phase.index.name = 'frame'

    return df_phase


def group_stance_frames(df_phase, suffix):
    """
    Create a DataFrame of stance frames grouped by contact number.

    Parameters
    ----------
    df_phase : DataFrame
        Index is 'frame'.
        Columns are 'phase', 'number', 'position'.
    suffix : str
        Suffix to add to values of the index ('_L' or '_R').

    Returns
    -------
    df_grouped : DataFrame
        Index values have the suffix appended.
        Columns are 'frame', 'position'

    Examples
    --------
    >>> pos = [[1, 2], [3, 4]]
    >>> d = {'phase': ['stance', 'stance'], 'number': [0, 0], 'position': pos}

    >>> df = pd.DataFrame(d, index=[175, 176])
    >>> df.index.name = 'frame'

    >>> group_stance_frames(df, '_L')
         frame    position
    0_L  175.5  [2.0, 3.0]

    """
    df_stance = df_phase[df_phase.phase == 'stance'].reset_index()

    column_funcs = {'frame': np.median, 'position': np.stack}
    df_grouped = pf.apply_to_grouped(df_stance, 'number', column_funcs)

    df_grouped.position = df_grouped.position.apply(np.median, axis=0)

    df_grouped.index = df_grouped.index.astype('str') + suffix

    return df_grouped


def get_contacts(foot_series, direction_pass, suffix):
    """
    Return a DataFrame containing contact frames and positions for one foot.

    A contact frame is when the foot is contacting the floor
    (in a stance phase).

    Parameters
    ----------
    foot_series : ndarray
        Index is 'frame'.
        Values are foot positions.
    direction_pass : ndarray
        Direction of motion for the walking pass.
    suffix : str
        Suffix indicating the foot side ('_L' or '_R').

    Returns
    -------
    DataFrame
        Index values have the suffix appended.
        Columns are 'frame', 'position'

    """
    df_phase = get_phase_dataframe(foot_series, direction_pass)

    return group_stance_frames(df_phase, suffix)
