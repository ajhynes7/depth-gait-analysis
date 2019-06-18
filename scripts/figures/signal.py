"""Plot the signal that is clustered to detect stance phases."""

from os.path import join

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from skspatial.transformation import transform_coordinates

import modules.cluster as cl
import modules.side_assignment as sa


def main():

    df_selected_passes = pd.read_pickle(join('data', 'kinect', 'df_selected_passes.pkl'))

    trial_name, num_pass = '2014-12-08_P006_Pre_001', 1

    df_pass = df_selected_passes.loc[(trial_name, num_pass)]
    frames = df_pass.index.values

    points_a = np.stack(df_pass.L_FOOT)
    points_b = np.stack(df_pass.R_FOOT)

    basis, frames_grouped, points_foot_grouped = sa.compute_basis(frames, points_a, points_b)

    signal_grouped = transform_coordinates(points_foot_grouped, basis.origin, [basis.forward])
    values_side_grouped = transform_coordinates(points_foot_grouped, basis.origin, [basis.perp])

    labels_grouped = cl.dbscan_st(signal_grouped, times=frames_grouped, eps_spatial=5, eps_temporal=10, min_pts=7)
    labels_grouped_l, labels_grouped_r = sa.assign_sides_grouped(frames_grouped, values_side_grouped, labels_grouped)

    is_noise = labels_grouped == -1

    fig_1 = plt.figure()

    plt.scatter(
        frames_grouped[~is_noise],
        signal_grouped[~is_noise],
        c=labels_grouped[~is_noise],
        cmap='Set1',
        edgecolor='k',
        s=75,
    )
    plt.scatter(frames_grouped[is_noise], signal_grouped[is_noise], c='k')

    plt.xlabel('Frame')
    plt.ylabel('Signal')

    fig_1.savefig(join('figures', 'signal_clustered.pdf'), dpi=1200)

    fig_2 = plt.figure()

    is_cluster_l = labels_grouped_l != -1
    is_cluster_r = labels_grouped_r != -1

    plt.scatter(frames_grouped[is_cluster_l], signal_grouped[is_cluster_l], c='b', edgecolor='k', s=75)
    plt.scatter(frames_grouped[is_cluster_r], signal_grouped[is_cluster_r], c='r', edgecolor='k', s=75)

    plt.xlabel('Frame')
    plt.ylabel('Signal')

    fig_2.savefig(join('figures', 'signal_sides.pdf'), dpi=1200)


if __name__ == '__main__':
    main()