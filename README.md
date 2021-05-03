# MAO Orchestrator

Distributed orchestrator for the [MAO-MAO collaborative research](https://mao-mao-research.github.io/) framework. Allows scheduled execution of containerized artefacts and semi-automatic data management workflows.
This implementation makes use of an etcd cluster for member discovery and metadata sharing and a simple git interface for managing data sets.

## Installation instructions

The orchestrator setup is controlled and build via docker-compose. However the user is provided with an interactive installer that asks for the necessary parameters to allow a quick and easy installation of a new MAO instance.

The setup process of a new MAO instance is composed of two steps:
- (optional, only necessary if new instance should join exiting federation) federation selection and making contact with operators for joining
- actual instance installation and federation join

If a user wants to join an existing MAO federation it is necessary to approach the federation operator before the installation of the new instance in order to negotiate certain parameters which are used by the installer to join the newly installed orchestrator with the existing federation. The selection of a desired federation to join is supported by the MAO installer which queries and presents existing federations based on the public MAO marketplace.

### Prerequisites

The MAO orchestrator has requirements that need to be present on the host system before the installation of a new instance:
- Python 3
- Docker
- Docker-Compose

### Installation

To run the installer use the following command:

```
python3 maoctl.py instance install
```

The installer will check the existence of the necessary dependencies and prompt the user for the installation parameters which are listed below for reference.

- **Selection - federate or standalone**: with this selection the user can choose either to install a standalone instance (e.g. to build up a new federation) or to join an existing MAO federation

Before the actual installation starts the installers will ask if the new instance is supposed to join an existing federation. If this is not the case you can skip this first step and the installation immediately starts. In case of a join request the installer will present a list of existing federations based on the MAO marketplace. After the selection of the desired federation to join it will present the necessary contact information that can be used in order to reach out to the federation operator that needs to prepare the join of a new instance. The installation process is suspended after this step and can be resumed after the necessary information is exchanged with the federation operator.

Installation parameters prompted by the installer:

- **MAO install directory**: directory on the host system to install the MAO instance to
- **MAO instance name**: can be freely chosen in case of new federation or standalone instance, if you like to join an existing one this has to be negotiated with the federation operator
- **Public IP**: IP address from which other systems can reach the new MAO instance
- **Git e-mail address**: used for the data-repository commits executed by the orchestrator
- ***SSH key directory***: path to the directory on the host that holds the SSH key pair used for git data-repository authentication

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
