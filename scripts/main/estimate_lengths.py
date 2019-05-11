"""Estimate lengths of the body for each trial."""

import time
from os.path import join

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist

import modules.iterable_funcs as itf
from modules.constants import PART_TYPES


def main():

    df_hypo = pd.read_pickle(join('data', 'kinect', 'df_hypo.pkl'))

    n_part_types = len(PART_TYPES)
    n_lengths = n_part_types - 1

    trials_to_run = df_hypo.index.levels[0]
    part_labels = range(n_part_types)

    df_lengths = pd.DataFrame(index=trials_to_run, columns=range(n_lengths))

    t = time.time()

    # %% Calculate lengths for each walking trial

    for trial_name, df_trial in df_hypo.groupby(level=0):

        n_frames = df_trial.shape[0]
        lengths_estimated = np.zeros((n_frames, n_lengths))

        for i, tuple_frame in enumerate(df_trial.itertuples()):

            population, labels = tuple_frame.population, tuple_frame.labels
            dist_matrix = cdist(population, population)

            for idx_a, idx_b in itf.pairwise(part_labels):

                distances = dist_matrix[labels == idx_a][:, labels == idx_b]

                if idx_a == 0:
                    # The first length is HEAD to HIP.
                    # The estimate is the median of the measured distances.
                    length_estimated = np.median(distances)
                else:
                    # The other length estimates are the
                    # first quartile of the measured distances.
                    length_estimated = np.percentile(distances, 25)

                lengths_estimated[i, idx_a] = length_estimated

        lengths_trial = np.median(lengths_estimated, axis=0)
        df_lengths.loc[trial_name] = lengths_trial

    df_lengths.to_csv(join('data', 'kinect', 'kinect_lengths.csv'))

    # %% Calculate run-time metrics

    time_elapsed = time.time() - t

    n_frames_total = df_hypo.shape[0]
    trials_run = len(trials_to_run)

    frames_per_second = round(n_frames_total / time_elapsed)

    print(
        """
        Number of trials: {}\n
        Number of frames: {}\n
        Total time: {}\n
        Frames per second: {}
        """.format(
            trials_run, n_frames_total, round(time_elapsed, 2), frames_per_second
        )
    )


if __name__ == '__main__':
    main()
