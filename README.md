# MAO Orchestrator

Distributed orchestrator for the [MAO-MAO collaborative research](https://mao-mao-research.github.io/) framework. Allows scheduled execution of containerized artefacts and semi-automatic data management workflows.
This implementation makes use of an etcd cluster for member discovery and metadata sharing and a simple git interface for managing data sets.

# Install instructions

The orchestrator setup is controlled and build via docker-compose. However the user is provided with an interactive installer that asks for the necessary parameters to allow a quick and easy installation of a new MAO instance.

If a user wants to join an existing MAO federation it is necessary to approach the federation operator before the installation of the new instance in order to negotiate certain parameters which are used by the installer to join the newly installed orchestrator with the existing federation:
- MAO instance name
- etcd configuration token

### Prerequisites

The MAO orchestrator has requirements that need to be present on the host system before the installation of a new instance:
- Python 3
- Docker
- Docker-Compose

### Installation

To run the installer use the following command:

```
python3 maoctl.py install
```

The installer will check the existence of the necessary dependencies and prompt the user for the installation parameters which are listed below for reference:
- **MAO install directory**: directory on the host system to install the MAO instance to
- **MAO instance name**: can be freely chosen in case of new federation or standalone instance, if you like to join an existing one this has to be negotiated with the federation operator
- **Public IP**: IP address from which other systems can reach the new MAO instance
- **Git e-mail address**: used for the data-repository commits executed by the orchestrator
- ***SSH key directory***: path to the directory on the host that holds the SSH key pair used for git data-repository authentication
- **Selection - federate or standalone**: with this selection the user can choose either to install a standalone instance (e.g. to build up a new federation) or to join an existing MAO federation

After this setup procedure the newly installed instance can be started via the commands provided by the installer.

# MAOCTL

The command-line client for the orchestrator can be used for either the native or docker-compose version to interact and issue commands to the orchestrator.
Use:
```
python3 maoctl.py --help
```
to begin.

# New Pipeline

The new pipeline is as yet NOT integrated with the client. Thus setting up and running a client must be done via direct HTTP requests for now.

Example:

- Register a tool as usual via the CLI:
```
python3 maoctl.py tool add ...
```
- Register a new dataset, this uses a new endpoint:
```
curl -X POST http://0.0.0.0:8080/registry/datasets  -H 'content-type: application/json' -d '{"name": "name-of-dataset", "body": {"master": "git-link", "nodes": []}}'
```
- Register a pipeline. This associates a tool with the dataset and creates a new branch with your username as the branch name.
```
curl -X POST http://0.0.0.0:8080/pipeline/init  -H 'content-type: application/json' -d '{"tool": "name-of-tool", "dataset":"name-of-dataset"}'
```

- Run the pipeline. You can use crontab syntax to use the persistent shceduler (this can be omitted to run in ad-hoc mode).
```
curl -X POST http://0.0.0.0:8080/pipeline/run  -H 'content-type: application/json' -d '{"name":"name-of-pipeline", "cron":"cron-string"}'
```

# Tool Compliance
To create tools that can be deployed to the MAO Orchestrator they need to comply with the following guidelines:
- Must be dockerized
- Must be able to launch with no interaction (the possibility to pass command line arguments may be added in a future update)
- Must put their generated data files in the `/usr/src/app/data` folder, as this is the folder mounted to the container.
