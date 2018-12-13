"""Combine walking trials and save to dataframes."""

import os

import pandas as pd


def combine_walking_trials(load_dir, matched_file_names):
    """Combine dataframes from all matched walking trials."""
    list_dfs = []

    for i, file_name in enumerate(matched_file_names):

        file_path = os.path.join(load_dir, file_name + '.pkl')

        df_device = pd.read_pickle(file_path)
        df_device['trial_id'] = i
        df_device['file_name'] = file_name

        list_dfs.append(df_device)

    return pd.concat(list_dfs).reset_index(drop=True)


def main():

    load_dir_k = os.path.join('data', 'kinect', 'gait_params')
    load_dir_z = os.path.join('data', 'zeno', 'gait_params')
    match_dir = os.path.join('data', 'matching')

    df_match = pd.read_csv(os.path.join(match_dir, 'match_kinect_zeno.csv'))

    # Convert match table to dictionary for easy file matching
    dict_match = {x.zeno: x.kinect for x in df_match.itertuples()}

    matched_file_names_k = list(dict_match.values())
    matched_file_names_z = list(dict_match.keys())

    df_total_k = combine_walking_trials(load_dir_k, matched_file_names_k)
    df_total_z = combine_walking_trials(load_dir_z, matched_file_names_z)

    # Extract date and participant from file name
    pattern = r'(?P<date>\d{4}-\d{2}-\d{2})_P(?P<participant>\d{3})'
    df_regex = df_total_k.file_name.str.extract(pattern)
    df_total_k = pd.concat((df_total_k, df_regex), axis=1, sort=False)

    # Convert dtypes of new columns
    df_total_k.participant = pd.to_numeric(df_total_k.participant)
    df_total_k.date = pd.to_datetime(df_total_k.date)

    # Remove negative values from Zeno data
    df_total_z = df_total_z.applymap(
        lambda x: abs(x) if isinstance(x, float) else x)

    # Drop column of stride numbers (not required for results)
    df_total_k = df_total_k.drop('stride', axis=1)
    df_total_z = df_total_z.drop('stride', axis=1)

    # Save total dataframes for easy analysis
    df_total_k.to_pickle(
        os.path.join('results', 'dataframes', 'df_total_k.pkl'))
    df_total_z.to_pickle(
        os.path.join('results', 'dataframes', 'df_total_z.pkl'))


if __name__ == '__main__':
    main()
