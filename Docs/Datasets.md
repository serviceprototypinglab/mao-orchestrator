# Working with datasets

The implementation of dataset management within the MAO Orchestrator is based on git repositories. Datasets can be registered to the cluster, making them known to all members, and from that point on a member can clone them onto their system.

## Getting information

You can request a list of datasets, or information on a single dataset.

### CLI

```
python maoctl.py dataset get
```
```
python maoctl.py dataset get <dataset>
```

### API

```
GET /datasets
```
#### Sample response

```
['data/dataset1','data/dataset2']
```
---
```
GET /datasets/<dataset>
```
#### Arguments

- **dataset**: The name of the dataset

#### Sample response

```
"https://gitihub.com/foo/bar"
```

## Register a dataset

Registering a dataset creates a new entry in etcd, letting all cluster members know about the dataset.
### CLI

```
python maoctl.py dataset add <name> <url>
```

### API

```
POST /regdata
```
#### Sample request
```
{
  "name": name,
  "url": url
}
```
#### Arguments

- **name**: The name of the dataset
- **url**: The URL of the dataset's git repo

#### Sample response

```
"https://gitihub.com/foo/bar"
```
## Un-register a dataset

Unregistering a dataset will remove it from etcd.
### CLI

```
python maoctl.py dataset remove <name>
```

### API

```
POST /datadelete
```
#### Sample request
```
{
  "name": name,
}
```
#### Arguments

- **name**: The name of the dataset

## List local datasets

List the datasets that have been cloned to the local filesystem.
### CLI

```
python maoctl.py dataset list-local
```

### API

```
GET /locallist
```
#### Sample response

```
{
  'dataset1': '/path/to/dataset1',
  'dataset2': '/path/to/dataset2'
}
```
