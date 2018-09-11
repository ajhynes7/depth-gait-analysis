"""Functions for assisting with the pandas library."""

from functools import reduce

import pandas as pd

import modules.numpy_funcs as nf
import modules.string_funcs as sf


def swap_columns(df, column_1, column_2):
    """
    Return a copy of a DataFrame with the values of two columns swapped.

    Parameters
    ----------
    df : DataFrame
        Input DataFrame.
    column_1, column_2 : str
        Names of the two columns to be swapped.

    Returns
    -------
    df_swapped : DataFrame
        DataFrame with swapped columns

    Examples
    --------
    >>> df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6], 'C': [7, 8, 9]})

    >>> swap_columns(df, 'A', 'B')
       A  B  C
    0  4  1  7
    1  5  2  8
    2  6  3  9

    """
    df_swapped = df.copy()

    df_swapped[[column_1, column_2]] = df[[column_2, column_1]]

    return df_swapped


def apply_to_columns(df_1, df_2, func):
    """
    Apply a function on each pair of matching columns from two DataFrames.

    Rows with NaN are removed before applying the function.

    Parameters
    ----------
    df_1, df_2 : DataFrame
        Input DataFrames.
    func : function
        Function that takes two numerical series as inputs.

    Returns
    -------
    dict_ : dict
        Each key is a column label.
        Each value is the output of the given function.

    Examples
    --------
    >>> df_1 = pd.DataFrame({'A': [5, 3], 'B': [2, 10]})
    >>> df_2 = pd.DataFrame({'A': [6, 4], 'B': [3, 2]})

    >>> dict_ = apply_to_columns(df_1, df_2, lambda a, b: a + b)

    >>> dict_['A']
    0    11
    1     7
    Name: A, dtype: int64

    >>> dict_['B']
    0     5
    1    12
    Name: B, dtype: int64

    """
    # Columns with numerical data
    numeric_columns_1 = df_1.select_dtypes(include='number').columns
    numeric_columns_2 = df_2.select_dtypes(include='number').columns

    shared_columns = set(numeric_columns_1) & set(numeric_columns_2)

    dict_ = {}
    for col in shared_columns:

        df_concat = pd.concat([df_1[col], df_2[col]], axis=1).dropna(axis=0)

        dict_[col] = func(df_concat.iloc[:, 0], df_concat.iloc[:, 1])

    return dict_


def drop_any_like(df, strings_to_drop, axis=0):
    """
    Drop labels that contain any of the input strings (case sensitive).

    Rows or columns can be dropped.

    Parameters
    ----------
    df : DataFrame
        Input DataFrame.
    strings_to_drop : iterable
        Sequence of strings to drop from the axis labels.
        A label that contains any of these strings will be dropped.
    axis : int, optional
        {index (0), columns (1)} (default 0).

    Returns
    -------
    DataFrame
        DataFrame with dropped rows or columns.

    Examples
    --------
    >>> df = pd.DataFrame({'Canada': [5, 3], 'UK': [2, 10]}, index=['A', 'B'])

    >>> drop_any_like(df, ['Can'], axis=1)
       UK
    A   2
    B  10

    >>> drop_any_like(df, ['B'], axis=0)
       Canada  UK
    A       5   2

    """
    labels = getattr(df, df._get_axis_name(axis))

    to_drop = [sf.any_in_string(x, strings_to_drop) for x in labels]

    df = df.drop(labels[to_drop], axis=axis)

    return df


def series_of_rows(array, *, index=None):
    """
    Place the rows of a numpy array into a pandas Series.

    Parameters
    ----------
    array : ndarray
        (n, d) array of n rows with length d.
    index : array_like, optional
        Index of the output series (default None).

    Returns
    -------
    series : Series
        Series with n elements.
        Each element in the series is an array of shape (d, ).

    Examples
    --------
    >>> import numpy as np
    >>> array = np.array([[1, 2], [2, 3], [5, 0], [10, 2]])

    >>> series_of_rows(array)
    0     [1, 2]
    1     [2, 3]
    2     [5, 0]
    3    [10, 2]
    dtype: object

    >>> series_of_rows(array, index=[1, 3, 5, 7])
    1     [1, 2]
    3     [2, 3]
    5     [5, 0]
    7    [10, 2]
    dtype: object

    """
    if index is None:
        index, _ = zip(*enumerate(array))

    series = pd.Series(index=index)
    series = series.apply(lambda x: [])

    for idx, vector in zip(series.index, array):

        series[idx] = vector

    return series


def merge_multiple(dataframes, **kwargs):
    """
    Merge multiple DataFrames together.

    Parameters
    ----------
    dataframes : iterable
        Each element is a DataFrame.

    Returns
    -------
    DataFrame
        Result of merging all DataFrames.

    Examples
    --------
    >>> df_1, df_2 = pd.DataFrame([1, 2, 3]), pd.DataFrame([4, 5, 6])
    >>> df_3, df_4 = pd.DataFrame([7, 8, 9]), pd.DataFrame([10, 11, 12])

    >>> dataframes = [df_1, df_2, df_3, df_4]

    >>> merge_multiple(dataframes, left_index=True, right_index=True)
       0_x  0_y  0_x  0_y
    0    1    4    7   10
    1    2    5    8   11
    2    3    6    9   12

    """
    return reduce(lambda a, b: pd.merge(a, b, **kwargs), dataframes)


def apply_to_grouped(df, groupby_column, column_funcs):
    """
    Apply functions to columns of a groupby object and combine the results.

    Parameters
    ----------
    df : DataFrame
        Input DataFrame.
    groupby_column : str
        Name of column to group.
    column_funcs : dict
        Each key is a column name.
        Each value is a function to apply to the column.

    Returns
    -------
    DataFrame
        Result of applying functions to each grouped column.
        Index is the groupby column.
        Columns are those specified as keys in the dictionary.

    Examples
    --------
    >>> d = {'letter': ['K', 'K', 'J'], 'number': [1, 2, 5], 'age': [1, 2, 3]}
    >>> df = pd.DataFrame(d)

    >>> apply_to_grouped(df, 'letter', {'number': min}).reset_index()
      letter  number
    0      J       5
    1      K       1

    """
    groupby_object = df.groupby(groupby_column)

    def yield_groups():
        """Inner function to yield results of applying func to the column."""
        for column, func in column_funcs.items():
            yield groupby_object[column].apply(func).to_frame()

    return merge_multiple(yield_groups(), left_index=True, right_index=True)


def split_column(df, *, column=0, delim=' ', new_columns=None, drop=True):
    """
    Split a column into multiple columns by splitting strings at a delimiter.

    Parameters
    ----------
    df : DataFrame
        Input DataFrame.
    column : {int, str}, optional
        Name of column to split (default 0).
    delim : str, optional
        Delimiter used to split column (default ' ').
    new_columns : iterable, optional
        Iterable of new column names (default None).
    drop : bool, optional
        If true, drop the original column that was split (default True).

    Returns
    -------
    df_final : DataFrame
        DataFrame including new columns from the split.

    Examples
    --------
    >>> df = pd.DataFrame(['1_2_3', '4_5_6'])

    >>> split_column(df, column=0, delim='_', drop=False)
           0  0  1  2
    0  1_2_3  1  2  3
    1  4_5_6  4  5  6

    >>> split_column(df, column=0, delim='_')
       0  1  2
    0  1  2  3
    1  4  5  6

    >>> split_column(df, column=0, delim='_', new_columns=['a', 'b', 'c'])
       a  b  c
    0  1  2  3
    1  4  5  6

    """
    df_split = df[column].str.split(delim, expand=True)

    if new_columns is not None:
        df_split.columns = new_columns

    if drop:
        df = df.drop(column, axis=1)

    df_final = pd.concat([df, df_split], axis=1)

    return df_final


def split_and_merge(df, merge_col=None, split_col=None, split_vals=None):
    """
    Split a DataFrame into two and merge the sub-DataFrames on a given column.

    The merge column is set as the index of the new DataFrame.

    Parameters
    ----------
    df : DataFrame
        Input DataFrame.
    merge_col : {int, str}, optional
        Column used to merge the two sub-DataFrames.
    split_col : {int, str}, optional
        Name of column used to split the DataFrame into two sub-DataFrames.
    split_vals : tuple, optional
        Values used to split the DataFrame.

    Returns
    -------
    df_merge : DataFrame
        Final DataFrame with suffixes on new columns.
        The merge column is set as the new index.

    Examples
    --------
    >>> d = {'group': ['A', 'A', 'B'], 'value': [1, 2, 3], 'number': [0, 1, 0]}
    >>> df = pd.DataFrame(d)

    >>> split_and_merge(df, 'number', 'group', ('A', 'B')).reset_index()
       number  value_A  value_B
    0       0        1      3.0
    1       1        2      NaN

    >>> split_and_merge(df, 'number', 'group', ('L', 'R')).reset_index()
    Empty DataFrame
    Columns: [number, value_L, value_R]
    Index: []

    """
    df_1 = df[df[split_col] == split_vals[0]]
    df_2 = df[df[split_col] == split_vals[1]]

    suffixes = ['_' + x for x in split_vals]

    df_merge = pd.merge(
        df_1,
        df_2,
        left_on=merge_col,
        right_on=merge_col,
        how='outer',
        suffixes=suffixes)

    df_merge = drop_any_like(df_merge, [split_col], axis=1)
    df_merge = df_merge.set_index(merge_col)

    return df_merge


def make_index_consecutive(df):
    """
    Make the values of a DataFrame index all consecutive.

    Parameters
    ----------
    df : DataFrame
        Input DataFrame.

    Returns
    -------
    df_consec : DataFrame
        DataFrame with a consecutive index.

    Examples
    --------
    >>> df = pd.DataFrame({'Col': [5, 6, 7]}, index=[1, 2, 4])
    >>> make_index_consecutive(df)
       Col
    1    5
    2    6
    3  NaN
    4    7

    """
    index_vals = df.index.values

    index_consec, _ = nf.make_consecutive(index_vals)

    df_consec = pd.DataFrame(index=index_consec, columns=df.columns)
    df_consec.update(df)

    return df_consec
