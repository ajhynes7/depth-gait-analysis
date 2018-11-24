"""Transform raw data from the Kinect into a pandas DataFrame."""

import os

import numpy as np
import pandas as pd

import analysis.images as im


def main():

    load_dir = os.path.join('data', 'kinect', 'raw')

    # Directories for all hypothetical points and highest confidence points
    save_dir_hypo = os.path.join('data', 'kinect', 'processed', 'hypothesis')

    part_types = ['HEAD', 'HIP', 'UPPER_LEG', 'KNEE', 'LOWER_LEG', 'FOOT']

    # Number of columns for the position coordinates
    # Number should be sufficiently large and divisible by 3
    n_coord_cols = 99

    # List of trials to run
    running_path = os.path.join('data', 'kinect', 'running',
                                'trials_to_run.csv')
    trials_to_run = pd.read_csv(running_path, header=None, squeeze=True).values

    for file_name in trials_to_run:

        file_path = os.path.join(load_dir, file_name + '.txt')

        df_raw = pd.read_csv(
            file_path,
            skiprows=range(22),
            header=None,
            names=[i for i in range(-2, n_coord_cols)],
            sep='\t',
            engine='python')

        # Change some column names
        df_raw.rename(columns={-2: 'Frame', -1: 'Part'}, inplace=True)

        # Replace any non-number strings with nan in the frame column
        df_raw.Frame = df_raw.Frame.replace(r'[^0-9]', np.nan, regex=True)

        # Convert the strings in the frame column so max function will work
        df_raw.Frame = pd.to_numeric(df_raw.Frame)

        max_frame = int(np.nanmax(df_raw.Frame))

        # Crop the DataFrame at the max frame number
        # (The text file loops back to the beginning)
        last_index = df_raw[df_raw.Frame == max_frame].index[-1]
        df_cropped = df_raw.loc[:last_index, :]

        df_cropped = df_cropped.set_index(['Frame', 'Part'])

        # Skip first 3 coordinate columns
        # (these are the coords selected by confidence, in image space)
        df_hypo_raw = df_cropped.iloc[:, 3:]

        # Drop rows with all nans
        df_hypo_raw = df_hypo_raw.dropna(how='all')

        # Frames with any position data
        frames = df_hypo_raw.index.get_level_values(0).unique()

        df_hypo_clean = pd.DataFrame(index=frames, columns=part_types)

        for frame in frames:
            for part_type in part_types:

                df_frame = df_hypo_raw.loc[frame]

                # Coordinates of the part type
                df_coords = df_frame[df_frame.index.str.contains(part_type)]

                if not np.all(np.isnan(df_coords)):

                    # Reshape into (n, 3) array
                    array_part = np.reshape(df_coords.values, (-1, 3))

                    # Drop rows with nan to get positions
                    points_hypo = array_part[
                        ~np.any(np.isnan(array_part), axis=1)]

                    df_hypo_clean.loc[frame, part_type] = points_hypo

                    # The hypothetical positions need to be converted from
                    # real to image then back to real using new parameters.
                    points_hypo = im.recalibrate_positions(
                        points_hypo, im.X_RES_ORIG, im.Y_RES_ORIG,
                        im.X_RES, im.Y_RES, im.F_XZ, im.F_YZ)

                    df_hypo_clean.loc[frame, part_type] = points_hypo

        # Rename some body parts to match names used in papers
        df_hypo_clean = df_hypo_clean.rename(
            columns={'UPPER_LEG': 'THIGH', 'LOWER_LEG': 'CALF'})

        save_path_hypo = os.path.join(save_dir_hypo, file_name) + '.pkl'
        df_hypo_clean.to_pickle(save_path_hypo)


if __name__ == '__main__':
    main()
