import numpy as np

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


def scatter_colour(points, colours, labels):
    """


    Parameters
    ----------


    Returns
    -------

    """
    plt.figure()

    for i, c in enumerate(colours):
        plt.scatter(points[i, 0], points[i, 1], color=c,
                    label='{i}'.format(i=labels[i]))

    plt.legend(loc='best')
    plt.show()


def scatter_pos(fig, point_list, colors='b'):
    """


    Parameters
    ----------


    Returns
    -------

    """

    ax = Axes3D(fig)

    # The z values of the points represent depth values,
    # while y values represent height
    # Thus, y and z are switched for plotting
    for i, points in enumerate(point_list):
        ax.scatter(points[:, 0], points[:, 2], points[:, 1],
                   c=colors[i], depthshade=False)

    ax.set_xlim3d(-100, 100)
    ax.set_ylim3d(100, 300)
    ax.set_zlim3d(-100, 100)

    ax.set_xlabel('X')
    ax.set_ylabel('Z')
    ax.set_zlabel('Y')


def scatter2(points):
    """
    Produce a 2D scatter plot from an array of points.

    Parameters
    ----------
    points : ndarray
        (n, d) array of n points in d dimensions.

    """
    plt.scatter(points[:, 0], points[:, 1])


def scatter_order(points, order):
    """
    Produce a scatter plot using a specified order of the (x, y) coordinates.

    Parameters
    ----------
    points : ndarray
        (n, d) array of n points in d dimensions.
    order : array_like
        Order of the coordinates

    """
    plt.scatter(points[:, order[0]], points[:, order[1]])


def scatter_dataframe(df):
    """
    Produce a scatter plot from a pandas DataFrame containing vectors.

    Parameters
    ----------
    df : pandas DataFrame
        Elements are vectors as 1D numpy arrays.
        Column names are used in the legend.

    """
    for column, values in df.items():
        points = np.vstack(values)

        scatter2(points)

    plt.legend(df.columns)


def plot_series(series):
    """
    Plot a pandas series containing vectors.

    Parameters
    ----------
    series : pandas Series
        Values are vectors as 1D numpy arrays.
        Index names are used in the legend.

    """
    # Array of points
    points = np.vstack(series)

    for point in points:

        plt.scatter(point[0], point[1])

    plt.legend(series.index)
