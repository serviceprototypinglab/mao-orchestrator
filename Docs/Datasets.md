# Working with datasets

The implementation of dataset management within the MAO Orchestrator is based on git repositories. Datasets can be registered to the cluster, making them known to all members, and from that point on a member can clone them onto their system.



## Getting information

You can request a list of datasets, or information on a single dataset.

### CLI

```
python maoctl.py dataset get
```
```
python maoctl.py dataset get --name NAME
```

## Register a dataset

Registering a dataset creates a new entry in etcd, letting all cluster members know about the dataset.
### CLI

```
python maoctl.py dataset add --name NAME --git_url URL
```

## Un-register a dataset

Unregistering a dataset will remove it from etcd.
### CLI

```
python maoctl.py dataset remove --name NAME
```

## List local datasets
*currently unsupported*

List the datasets that have been cloned to the local filesystem.

### CLI

```
python maoctl.py dataset list-local
```
## Clone a registered dataset
*currently unsupported*

This will clone the specified dataset to the import directory set in the configuration file.

### CLI
```
python maoctl.py dataset clone <name>
```
## Delete a cloned dataset
*currently unsupported*

Delete a cloned dataset from the local filesystem.
### CLI
```
python maoctl.py dataset remove-local <name>
```
