"""
Functions involving a sliding window.

The window contains n elements from a larger iterable.

"""

import itertools
from typing import Iterable, Iterator, Tuple


def generate_window(it: Iterable, n: int = 2) -> Iterator[Tuple]:
    """
    Generate a sliding window of width n from an iterable.

    Adapted from an itertools recipe.

    Parameters
    ----------
    it : iterable
        Input sequence.
    n : int, optional
        Width of sliding window (default 2).

    Yields
    ------
    result : tuple
        Tuple containing n elements from input sequence.

    """
    iterator = iter(it)

    result = tuple(itertools.islice(iterator, n))

    if len(result) == n:
        yield result

    for elem in iterator:

        result = result[1:] + (elem,)

        yield result
