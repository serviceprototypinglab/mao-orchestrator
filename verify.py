import pandas as pd
import numpy as np
import glob
import json
from pandas.api.types import is_numeric_dtype


def validate(prefix, idx, metrics, props, filenames):
    filenames.sort()
    n = len(filenames)
    dfs = []
    for filename in filenames:
        df_temp = pd.read_csv(filename)
        df_temp['node_id'] = filename.split('/')[-2]
        dfs.append(df_temp)
    df = pd.concat(dfs)
    print(len(df))
    idxs = df[idx].unique()
    print(len(idxs))
    # Get duplicate rows by index
    outliers = []
    for index in idxs:
        rows = df.loc[df[idx] == index]
        # Find outliers
        for field in rows:
            if field != idx and is_numeric_dtype(rows[field]) and n > 10:
                mean = rows[field].mean()
                std = rows[field].std()
                for value in rows[field]:
                    if value < mean - 3 * std or value > mean + 3 * std:
                        outliers.append([index, field, value])
            elif field != idx and field != 'node_id' and not is_numeric_dtype(rows[field]):
                votes = {}
                for value in rows[field]:
                    if value not in votes:
                        votes[value] = 1
                    else:
                        votes[value] += 1
                winner = max(votes.keys(), key=(lambda k: votes[k]))
                for value in rows[field]:
                    if value != winner:
                        outliers.append([index, field, value])
    outlier_json = []
    for item in outliers:
        item.append(df.loc[(df[idx] == item[0]) & (df[item[1]] == item[2])]['node_id'].values[0])
        print(item)
        outlier_json.append(item)
        df.loc[(df[idx] == item[0]) & (df[item[1]] == item[2]), item[1]] = np.NaN
    with open(f'{prefix}_outliers.json', 'w') as outlier_file:
        json.dump(outlier_json, outlier_file)
    df.to_csv(f'{prefix}_concat_no_outliers.csv')
    mean = df.groupby(idx).mean()
    maxv = df.groupby(idx).max()
    min = df.groupby(idx).min()
    minmax = min.join(maxv, on=idx, lsuffix='_min', rsuffix='_max')
    mean.columns += '_mean'
    result = minmax.join(mean, on=idx)
    df.drop(metrics + ['node_id'], axis=1, inplace=True)
    # dedupe to leave only one row with each combination of group_cols
    # in df
    df.drop_duplicates(subset=[idx] + props, keep='last', inplace=True)
    for prop in props:
        df = df[df[prop].notnull()]
    # add the mean columns from aggs into df
    df = df.merge(right=mean, right_index=True, left_on=[idx], how='right')
    result.to_csv(f'{prefix}_aggregate.csv')
    df.to_csv(f'{prefix}_mean.csv')
