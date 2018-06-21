import os
import glob

import pandas as pd

import modules.general as gen
import modules.pose_estimation as pe


def main():

    for file_path in file_paths[50:]:

        df = pd.read_pickle(file_path)

        # Select frames with data
        lower_parts, part_labels = gen.strings_with_any_substrings(
            df.columns, lower_part_types)

        df_lower = df[lower_parts].dropna(axis=0)

        population_series = df_lower.apply(
            lambda row: pe.get_population(row, part_labels)[0], axis=1)

        label_series = df_lower.apply(
            lambda row: pe.get_population(row, part_labels)[1], axis=1)

        # Estimate lengths between consecutive parts
        lengths = pe.estimate_lengths(population_series, label_series,
                                      cost_func, 60, eps=0.01)

        # %% Fill in row of results DataFrame

        df_metrics = pd.read_csv(save_path, index_col=0)

        base_name = os.path.basename(file_path)     # File with extension
        file_name = os.path.splitext(base_name)[0]  # File with no extension

        df_metrics.loc[file_name] = lengths

        df_metrics.to_csv(save_path)


if __name__ == '__main__':

    # %% Parameters

    def cost_func(a, b): return (a - b)**2

    lower_part_types = ['HEAD', 'HIP', 'UPPER_LEG', 'KNEE', 'LOWER_LEG',
                        'FOOT']

    # %% Reading data

    save_name = 'kinect_lengths.csv'

    load_dir = os.path.join('data', 'kinect', 'processed', 'hypothesis')
    save_dir = os.path.join('data', 'results')

    # All files with .pkl extension
    file_paths = glob.glob(os.path.join(load_dir, '*.pkl'))

    save_path = os.path.join(save_dir, save_name)

    # %% Run main script

    main()