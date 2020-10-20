import os
import json
import glob
import verify


def consensus(path):
    dirs = [f.path for f in os.scandir(path) if f.is_dir() and "__" not in f.path]
    #print(dirs)
    dirs.sort()
    with open(f"{dirs[0]}/meta.json") as meta:
        data = json.load(meta)
    #print(data)
    for item in data:
        prefix = item['prefix']
        index = item['index']
        metrics = item['metrics']
        props = item['props']
        candidates = []
        for dir in dirs:
            files = glob.glob(f"{dir}/{prefix}*.csv")
            files.sort()
            candidates.append(files[-1])
        print(candidates)
        verify.validate(prefix, index, metrics, props, candidates)
