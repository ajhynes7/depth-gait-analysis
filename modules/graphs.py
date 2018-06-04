import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist

from modules.general import pairwise


def adj_list_to_matrix(G):
    """
    Convert an adjacency list to an adjacency matrix.

    Parameters
    ----------
    G : dict
        Adjacency list.
        G[u][v] is the weight from node u to node v.
        Each node u in the graph must be a key in G.

    Returns
    -------
    M : ndarray
        Adjacency matrix.

    Examples
    --------
    >>> G = {0: {}, 1: {}, 2: {1: 10}}

    >>> adj_list_to_matrix(G)
    array([[nan, nan, nan],
           [nan, nan, nan],
           [nan, 10., nan]])
    """
    n_nodes = len(G)

    M = np.full((n_nodes, n_nodes), np.nan)

    for u in G:
        for v in G[u]:
            M[u, v] = G[u][v]

    return M


def adj_matrix_to_list(M):
    """
    Convert an adjacency matrix to an adjacency list.

    Parameters
    ----------
    M : array_like
        (n, n) adjacency matrix of n nodes.

    Returns
    -------
    G : dict
        Adjacency list.
        G[u][v] is the weight from node u to node v.

    Examples
    --------
    >>> M = [[np.nan, 3, 10], [np.nan, np.nan, 5], [np.nan, np.nan, np.nan]]

    >>> adj_matrix_to_list(M)
    {0: {1: 3, 2: 10}, 1: {2: 5}, 2: {}}
    """

    n_nodes = len(M)
    G = {i: {} for i in range(n_nodes)}

    for u in range(n_nodes):
        for v in range(n_nodes):
            element = M[u][v]

            if ~np.isnan(element):
                G[u][v] = element

    return G


def dag_shortest_paths(G, order, source_nodes):
    """
    Compute shortest path to each node on a directed acyclic graph.

    Parameters
    ----------
    G : dict
        Adjacency list.
        G[u][v] is the weight from node u to node v.
        Each node u in the graph must be a key in G.
    order : list
        Topological ordering of the nodes.
        For each edge u to v, u comes before v in the ordering.
    source_nodes : set
        Set of source nodes.
        The shortest path can begin at any of these nodes.

    Returns
    -------
    prev : dict
        For each node u in the graph, prev[u] is the previous node
        on the shortest path to u.
    dist : dict
        For each node u in the graph, dist[u] is the total distance (weight)
        of the shortest path to u.

    Examples
    --------
    >>> G = {0: {1: 10, 2: 20}, 1: {3: 5}, 2: {3: 8, 8: 15}, 3: {8: 6}, 8: {}}
    >>> order = G.keys()
    >>> source_nodes = {0, 1}

    >>> prev, dist = dag_shortest_paths(G, order, source_nodes)

    >>> prev
    {0: nan, 1: nan, 2: 0, 3: 1, 8: 3}

    >>> dist
    {0: 0, 1: 0, 2: 20, 3: 5, 8: 11}

    """
    dist = {v: np.inf for v in G}
    prev = {v: np.nan for v in G}

    for v in source_nodes:
        dist[v] = 0

    for u in order:
        for v in G[u]:
            weight = G[u][v]

            if dist[v] > dist[u] + weight:
                # Relax the edge
                dist[v] = dist[u] + weight
                prev[v] = u

    return prev, dist


def trace_path(prev, target_node):
    """
    Trace back a path through a graph.

    Parameters
    ----------
    prev : dict
        For each node u in the graph, prev[u] is the previous node
        on the path to u.
    target_node : any type
        Last node in the path.

    Returns
    -------
    list
        Path from source to last node.

    Examples
    --------
    >>> prev = {'a': np.nan, 'b': np.nan, 'c': 'a', 'd': 'b', 'e': 'd'}

    >>> trace_path(prev, 'e')
    ['b', 'd', 'e']

    """
    u, path = target_node, [target_node]

    while pd.notnull(u):

        u = prev[u]
        path.append(u)

    # Exclude the last element because it is NaN (no previous node)
    path = path[:-1]

    # Reverse the list to get the path in order
    return path[::-1]


def weight_along_path(G, path):
    """
    Compute the total weight of a path in a graph.

    Parameters
    ----------
    G : dict
        Adjacency list.
        G[u][v] is the weight from node u to node v.
    path : array_like
        List of nodes comprising a path on graph G.

    Returns
    -------
    total_weight : {float, int}
        The sum of weights along the path.

    Examples
    --------
    >>> G = {0: {1: 10, 2: 20}, 1: {3: 5}, 2: {3: 8}, 3: {8: 6}, 8: {}}
    >>> path = [0, 1, 3, 8]

    >>> weight_along_path(G, path)
    21
    """

    total_weight = 0

    for a, b in pairwise(path):
        total_weight += G[a][b]

    return total_weight


def labelled_nodes_to_graph(nodes, labels, label_adj_list):
    """
    Create an adjacency list from a set of labelled nodes.
    The weight between pairs of labels is specified.

    If nodes u and v have labels A and B,
    and this pair of labels invokes a weight of w,
    then the output adjacency list has a weight of w from node u to node v.

    Parameters
    ----------
    nodes : array_like
        List of nodes in the graph.
    node_labels : array_like
        Label of each node.
    label_adj_list : dict
        Adjacency list for the labels.
        label_adj_list[A][B] is the weight from label A to label B

    Returns
    -------
    G : dict
        Adjacency list.

    Examples
    --------
    >>> nodes = [10, 11, 12, 13]
    >>> labels = [1, 1, 1, 2]

    >>> label_adj_list = {1: {2: 10}, 2: {3: 5}, 3: {}}

    >>> labelled_nodes_to_graph(nodes, labels, label_adj_list)
    {10: {13: 10}, 11: {13: 10}, 12: {13: 10}, 13: {}}

    """
    G = {v: {} for v in nodes}

    for u, label_u in zip(nodes, labels):
        for v, label_v in zip(nodes, labels):

            if label_v in label_adj_list[label_u]:

                G[u][v] = label_adj_list[label_u][label_v]

    return G


def points_to_graph(points, labels, expected_dists, weight_func):
    """
    Construct a weighted graph from a set of labelled points in space.

    Parameters
    ----------
    points : ndarray
        List of points in space.
    labels : array_like
        Label of each point.
    expected_dists : dict
        The expected distance between pairs of labels.
        expected_dists[A][B] is the expected distance from a
        point with label A to a point with label B.
    cost_func : function
        Cost function that takes two arrays as input.

    Returns
    -------
    dict
        Graph representation of the points as an adjacency list.

    Examples
    --------
    >>> points = np.array([[0, 3], [0, 10], [2, 3]])
    >>> labels = [0, 1, 1]
    >>> expected_dists = {0: {1: 5}, 1: {}}
    >>> weight_func = lambda a, b: abs(a - b)

    >>> points_to_graph(points, labels, expected_dists, weight_func)
    {0: {1: 2.0, 2: 3.0}, 1: {}, 2: {}}

    """
    nodes = [i for i, _ in enumerate(labels)]

    # Expected distances between points
    adj_list_expected = labelled_nodes_to_graph(nodes, labels, expected_dists)
    dist_matrix_expected = adj_list_to_matrix(adj_list_expected)

    # Measured distances between all points
    dist_matrix = cdist(points, points)

    # Adjacency matrix defined by a weight function
    adj_matrix = weight_func(dist_matrix, dist_matrix_expected)

    return adj_matrix_to_list(adj_matrix)


if __name__ == "__main__":

    import doctest
    doctest.testmod()