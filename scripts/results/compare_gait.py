"""Create plots and tables for comparing Kinect to Zeno Walkway."""

from os.path import join

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import analysis.stats as st


def main():

    dir_plots = join('results', 'plots')
    dir_tables = join('results', 'tables')

    # Gait parameters from all trials with matching IDs
    df_trial_id_k = pd.read_pickle(join('data', 'kinect', 'df_trial_id.pkl'))
    df_trial_id_z = pd.read_pickle(join('data', 'zeno', 'df_trial_id.pkl'))

    gait_params = df_trial_id_k.select_dtypes(float).columns

    # Median gait parameters of each walking trial
    df_trials_k = df_trial_id_k.groupby(level=0).median()
    df_trials_z = df_trial_id_z.groupby(level=0).median()

    list_bland_tuples = []
    dict_icc = {f'icc_{x}1': {} for x in ['2', '3']}

    for param in gait_params:

        measures_k = df_trials_k[param]
        measures_z = df_trials_z[param]
        measures = np.column_stack((measures_k, measures_z))

        means = (measures_k + measures_z) / 2
        differences = st.relative_difference(measures_k, measures_z)
        bland_alt = st.bland_altman(differences)

        list_bland_tuples.append(bland_alt)

        dict_icc['icc_21'][param] = st.icc(measures, form=(2, 1))
        dict_icc['icc_31'][param] = st.icc(measures, form=(3, 1))

        # %% Bland-Altman plot

        fig_1, ax_1 = plt.subplots()

        ax_1.scatter(means, differences, c='k', s=20)

        # Horizontal lines for bias and limits of agreement
        ax_1.axhline(y=bland_alt.bias, color='k', linestyle='-')
        ax_1.axhline(y=bland_alt.lower_limit, color='k', linestyle=':')
        ax_1.axhline(y=bland_alt.upper_limit, color='k', linestyle=':')

        # Enlarge y range
        y_lims = np.array(ax_1.get_ylim())
        y_range = y_lims[1] - y_lims[0]
        ax_1.set_ylim(y_lims + 0.5 * y_range * np.array([-1, 1]))

        # Reduce number of ticks on the axes, so that figure can be small
        ax_1.locator_params(nbins=5)

        ax_1.tick_params(labelsize=25)  # Increase font of tick labels

        # Format y labels as percentages.
        # This line needs to be after the others,
        # or else the y-axis may be incorrect.
        ax_1.set_yticklabels([f'{(x * 100):.0f}'
                              for x in ax_1.get_yticks()])

        # Remove right and top borders
        ax_1.spines['right'].set_visible(False)
        ax_1.spines['top'].set_visible(False)

        plt.xlabel('Mean of two measurements [cm]', fontsize=30)
        plt.ylabel(r'Relative difference [\%]', fontsize=30)
        plt.tight_layout()

        fig_1.savefig(join(dir_plots, 'bland_{}.png'.format(param)))

        # %% Direct comparison plots

        fig_2, ax_2 = plt.subplots()

        ax_2.scatter(measures_z, measures_k, c='k', s=20)

        lims = [
            np.min([ax_2.get_xlim(), ax_2.get_ylim()]),
            np.max([ax_2.get_xlim(), ax_2.get_ylim()]),
        ]

        # Plot equality line
        ax_2.plot(lims, lims, 'k-')

        # Remove right and top borders
        plt.gca().spines['right'].set_visible(False)
        plt.gca().spines['top'].set_visible(False)

        ax_2.tick_params(labelsize=25)

        plt.xlabel("Zeno Walkway [cm]", fontsize=30)
        plt.ylabel("Kinect [cm]", fontsize=30)
        plt.tight_layout()

        fig_2.savefig(join(dir_plots, 'compare_{}.png'.format(param)))

    # %% Create tables of results

    df_bland_alt = pd.DataFrame.from_records(
        list_bland_tuples, index=gait_params, columns=bland_alt._fields
    )

    df_icc = pd.DataFrame.from_dict(dict_icc)

    with open(join(dir_tables, 'bland_altman.txt'), 'w') as file:
        file.write(np.round(df_bland_alt, 3).to_latex())

    with open(join(dir_tables, 'icc.txt'), 'w') as file:
        file.write(np.round(df_icc, 3).to_latex())


if __name__ == '__main__':
    main()
