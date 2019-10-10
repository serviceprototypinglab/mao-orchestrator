# MAO-MAO-Framework

MAO-MAO collaborative research framework. Allows scheduled execution of periodic data collectors and has built-in spike detection for the data.
This implementation makes use of an etcd cluster for member discovery, persistence and metadata sharing and a simple git interface for cloning data sets.

## Install instructions

- Install etcd and start a cluster (or join the production cluster once it exists)
```
sudo apt install etcd-server
etcd
```
- Setup your importdir and etcd settings in config.ini . Importdir is where your local data will be stored.
- `pip3 install -r requirements.txt`

#### Starting the framework:
To launch the framework:
```
python3 async_launcher.py
```
At this stage it runs in the foreground so you will need a new terminal.

## Using the CLI
Interacting with the server is done via **maoctl**.

At the top level there are 2 main commands, for interacting with tools or datasets.
```
usage: maoctl.py [-h] {tool,dataset} ...

positional arguments:
  {tool,dataset}  Available commands
    tool          List, register or run tools
    dataset       List, register or retrieve dataset

optional arguments:
  -h, --help      show this help message and exit
```
### Interacting with tools
```
usage: maoctl.py tool [-h] {get,add,run,schedule} ...

positional arguments:
  {get,add,run,schedule}
                        Tool-related commands
    get                 List tools
    add                 Register a new tool
    run                 Execute a tool immediately
    schedule            Schedule a tool to run periodically

optional arguments:
  -h, --help            show this help message and exit
```
#### Register a new tool
```
usage: maoctl.py tool add [-h] name author image data_repo code_repo artefact

positional arguments:
  name        Name of the tool to register
  author      Name of the author of the tool
  image       Docker image with which to invoke the tool
  data_repo   Associated data repository. Will be cloned on first invocation
  code_repo   Code repository for the tool's source code
  artefact    The type of artefact targeted by the tool

optional arguments:
  -h, --help  show this help message and exit
```
#### Run a tool immediately
```
usage: maoctl.py tool run [-h] name

positional arguments:
  name        Name of the tool to run

optional arguments:
  -h, --help  show this help message and exit
```
#### Schedule to run a tool periodically
```
usage: maoctl.py tool schedule [-h] name {daily,weekly}

positional arguments:
  name            Name of the tool to schedule
  {daily,weekly}  Execution schedule: daily/weekly

optional arguments:
  -h, --help      show this help message and exit
```
### Interacting with datasets
```
usage: maoctl.py dataset [-h] {get,add,clone} ...

positional arguments:
  {get,add,clone}  Dataset-related commands
    get            List datasets
    add            Register a new dataset
    clone          Clone a dataset

optional arguments:
  -h, --help       show this help message and exit
```
#### Register a dataset
```
usage: maoctl.py dataset add [-h] name url

positional arguments:
  name        Name of the dataset to register
  url         Github remote to clone the dataset

optional arguments:
  -h, --help  show this help message and exit
```
#### Clone a dataset locally
```
usage: maoctl.py dataset clone [-h] name

positional arguments:
  name        Name of the dataset to retrieve

optional arguments:
  -h, --help  show this help message and exit
```
