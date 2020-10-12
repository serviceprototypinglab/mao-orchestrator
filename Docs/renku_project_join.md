# Joining an existing MAO-Renku project

## Fork the project on Renku

Follow the [Renku docs](https://renku.readthedocs.io/en/latest/). The process is similar to forking a public git repo.

## Register the fork in MAO

Use the maoctl to register the new fork under the parent dataset (dataset lineage is important for the WIP federated data auditing feature):

```
python3 maoctl.py data add <parent-dataset-name> <your-node-name> <git-link>
```

## Run using the fork

You can add optional parameters to the run command so it overrides the default repo with your fork:

```
python3 maoctl.py tool run <your-tool> --renku --dataset <parent-dataset-name> --node <your-node-name>
```

## Notes

**Switching forks is not yet supported.** It is recommended you back-up the data files and delete them from your MAO datadir, then remove the data entry from MAO's `config.ini` file before running with a different fork. This will only reset the tool for your MAO node and will have no effect on the shared registry, so **other nodes will not be affected**.
