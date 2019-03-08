"""Plot label and depth images with body segment centroids."""

import glob
import os
import pickle
import re
from os.path import join

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist

import analysis.images as im
import analysis.plotting as pl
import modules.pose_estimation as pe
from scripts.main.select_proposals import cost_func, score_func


def main():

    kinect_dir = join('data', 'kinect')

    load_dir = join(kinect_dir, 'labelled_trials')
    hypo_dir = join(kinect_dir, 'processed', 'hypothesis')
    align_dir = join(kinect_dir, 'alignment')

    part_types = ['Head', 'Hip', 'Thigh', 'Knee', 'Calf', 'Foot']
    part_connections = np.array(
        [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [3, 5], [1, 3]]
    )

    legend_location = [0.2, 0.6]

    file_index = 271

    labelled_trial_names = os.listdir(load_dir)
    trial_name = labelled_trial_names[0]

    # DataFrame with lengths between body parts
    df_lengths = pd.read_csv(
        join(kinect_dir, 'lengths', 'kinect_lengths.csv'), index_col=0
    )
    lengths = df_lengths.loc[trial_name]

    depth_dir = join(load_dir, trial_name, 'depth16bit')
    depth_paths = sorted(glob.glob(join(depth_dir, '*.png')))

    depth_path = depth_paths[file_index]
    depth_image = cv2.imread(depth_path, cv2.IMREAD_ANYDEPTH)
    df_hypo = pd.read_pickle(join(hypo_dir, trial_name) + '.pkl')

    match_object = re.search(r'(\d+).png', depth_path)
    image_number = int(match_object.group(1))

    # Load dictionary to convert image numbers to frames
    with open(join(align_dir, "{}.pkl".format(trial_name)), 'rb') as handle:
        image_to_frame = pickle.load(handle)

    frame = image_to_frame[image_number]

    hypotheses = df_hypo.loc[frame]

    part_labels = range(len(part_types))
    population, labels = pe.get_population(hypotheses, part_labels)

    points_image = np.apply_along_axis(
        im.real_to_image, 1, population, im.X_RES, im.Y_RES, im.F_XZ, im.F_YZ
    )

    # %% Plot joint proposals on depth image

    fig = plt.figure()
    plt.imshow(depth_image, cmap='gray')
    pl.scatter_labels(points_image[:, :2], labels, edgecolors='k', s=100)
    plt.legend(part_types, framealpha=1, loc='upper left', fontsize=12)
    plt.axis('off')
    fig.savefig(join('figures', 'joint_proposals_image.pdf'))

    # %% Plot joint proposals

    fig = plt.figure()
    pl.scatter_labels(population, labels, edgecolor='k', s=50)
    plt.axis('equal')
    plt.axis('off')
    plt.legend(part_types, loc=legend_location, edgecolor='k')
    fig.savefig(join('figures', 'joint_proposals.pdf'), dpi=1200)

    # %% Plot reduced joint proposals

    # Expected lengths for all part connections,
    # including non-adjacent (e.g., knee to foot)
    label_adj_list = pe.lengths_to_adj_list(part_connections, lengths)

    # Define a graph with edges between consecutive parts
    # (e.g. knee to calf, not knee to foot)
    cons_label_adj_list = pe.only_consecutive_labels(label_adj_list)

    # Run shortest path algorithm on the body graph
    prev, dist = pe.pop_shortest_paths(
        population, labels, cons_label_adj_list, cost_func
    )

    # Get shortest path to each foot
    paths, _ = pe.paths_to_foot(prev, dist, labels)

    pop_reduced, paths_reduced = pe.reduce_population(population, paths)
    labels_reduced = labels[np.unique(paths)]

    fig = plt.figure()
    pl.scatter_labels(pop_reduced, labels_reduced, edgecolor='k', s=50)
    plt.axis('equal')
    plt.axis('off')
    fig.savefig(join('figures', 'joint_proposals_reduced.pdf'), dpi=1200)

    # %% Plot spheres

    r = 10
    pairs = [[0, 1], [2, 3], [1, 2]]

    n_pop_reduced = pop_reduced.shape[0]
    path_vectors = pe.get_path_vectors(paths_reduced, n_pop_reduced)

    dist_matrix = cdist(pop_reduced, pop_reduced)
    score_matrix = pe.get_scores(
        dist_matrix, paths_reduced, label_adj_list, score_func
    )

    n_figs = len(pairs)

    for i in range(n_figs):
        fig, ax = plt.subplots()

        pl.scatter_labels(
            pop_reduced, labels_reduced, s=50, edgecolor='k', zorder=5
        )

        if i == 0:
            # Add legend to first figures
            plt.legend(part_types, loc=legend_location, edgecolor='k')

        has_sphere = np.any(path_vectors[pairs[i]], 0)
        within_radius = dist_matrix < r

        inside_spheres = pe.in_spheres(within_radius, has_sphere)
        pl.plot_links(pop_reduced, score_matrix, inside_spheres)

        has_sphere = np.any(path_vectors[pairs[i]], 0)
        pl.plot_spheres(pop_reduced[has_sphere], r, ax)

        plt.axis('equal')
        plt.axis('off')

        save_path = join('figures', 'spheres_{}.pdf')
        fig.savefig(save_path.format(i), dpi=1200)


if __name__ == '__main__':
    main()
