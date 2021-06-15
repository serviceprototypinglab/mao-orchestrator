# MAO Orchestrator

Distributed orchestrator for the [MAO-MAO collaborative research](https://mao-mao-research.github.io/) framework. Allows scheduled execution of containerized artefacts and semi-automatic data management workflows.
This implementation makes use of an etcd cluster for member discovery and metadata sharing and a simple git interface for managing data sets.

## MAO Glossary

- **MAO Federation**
  - a group of 1 to n MAO nodes that work on a shared set of tasks
  - the nodes within a federation share data trough the federated etcd instances and the git-based datasets
- **MAO Instance**
  - a node that is running an instance of the MAO orchestrator within a MAO federation
  - a MAO instances is composed of the following components:
    - orchestrator: offers a REST based HTTP API to interact with different MAO components
    - executor: handles the Docker-based execution of tools on a specific instance
    - etcd: key-value store that is shared with might existing other instances in a federation
    - PostgreSQL: database that hold instance local information (e.g. pipelines, schedules etc.)
- **MAO Tool**
  - a tool is basically a Docker container that includes the necessary code to perform a tasks that helps a federation to accomplish its work and goals
- **MAO Dataset**
  - a MAO dataset is git repository that can serve as an input or output for a single MAO pipeline step
  - datasets can be shared (via a repository server) across different nodes within a federation or be instance local
- **MAO Pipeline**
  - a MAO pipeline consists of 1 to n subsequent steps that might have an input dataset but have to have an output dataset that serves as result container for the work done during the step execution
  - each pipeline step refers to a single tool that is used to execution the steps purpose
  - additionally to the main components of a step (datasets and tool) the following options can be provided
    - command: defines a custom command that is executed within the tool container
    - environment variables: a set of environment variables that can be used to configure the tool running during the step execution

## Installation instructions

The orchestrator setup is controlled and build via docker-compose. However the user is provided with an interactive installer that asks for the necessary parameters to allow a quick and easy installation of a new MAO instance.

The setup process of a new MAO instance is composed of two steps:
- (optional, only necessary if new instance should join exiting federation) federation selection and making contact with operators for joining
- actual instance installation and federation join

If a user wants to join an existing MAO federation it is necessary to approach the federation operator before the installation of the new instance in order to negotiate certain parameters which are used by the installer to join the newly installed orchestrator with the existing federation. The selection of a desired federation to join is supported by the MAO installer which queries and presents existing federations based on the public MAO marketplace. Details can be found below in the `Installation` section.

### Prerequisites

The MAO orchestrator has requirements that need to be present on the host system before the installation of a new instance. The following section list these requirements and tries to describe how to get them for your specific setup.

- Python 3.6+ (including `pip`)
  - the hosting system needs a fairly recent version of Python in order to run the installer and initialization scripts that ease the setup process
  - the actual MAO orchestrator Python version and dependencies are handled within the MAO Docker containers that are maintained by the MAO team without any additional user interaction required
  - if your distribution provides a recent version of Python please refer to your distributions documentation and use the package manager to install it, e.g. see command below for Ubuntu - otherwise you can find the most recent Python version [here](https://www.python.org/downloads/):
```
sudo apt-get install python3 python3-pip
```
- Docker
  - all MAO tools and the orchestrator together with its dependencies are shipped as Docker containers, therefore the host system needs to have the Docker engine installed in order to be able to execute those
  - if your distribution provides a recent version of the Docker Engine please refer to your distributions documentation and use the package manager to install it - otherwise you can find more information on how to install Docker [here](https://docs.docker.com/engine/install/)
- Docker-Compose
  - the MAO orchestrator consists of several components (orchestrator itself, PostgreSQL database, tool executor, etcd instance etc.) that need some plumping in order to work together correctly. To ease the management of this multi-component setup MAO organizes the different components along with the necessary plumbing using Docker-Compose.
  - if your distribution provides a recent version of Docker-Compose please refer to your distributions documentation and use the package manager to install it - otherwise you can find more information on how to install Docker-Compose [here](https://docs.docker.com/compose/install/)
- Git
  - if you want to use git to download the MAO orchestrator to your system please refer to your distributions documentation and use the package manager to install it
  - otherwise you can use the GitHub project download feature to generate an archive that you can download on your host system

### Installation

Download or clone this git repository to your hosting system via the following command and change into the newly created directory:
```
git clone https://github.com/serviceprototypinglab/mao-orchestrator
```

> :warning: **The following Docker image build is subject to change**: This step will not be necessary with the public release of the MAO installer.

Currently the MAO orchestrator images (namely `orchestrator` and `executor`) are not released to a public Docker registry. They currently need to build manually on the new instance locally with the following commands:

```
docker build -t local/mao -f Dockerfile .
docker build -t local/executor -f Dockerfile_executor .
```

In order to run the installer some Python dependencies have to be installed in order for the installer to run correctly:
- the installer is shipped with a separate pip requirements file called `requirements_installer.txt`. You can use the following command with `pip` or `pip3` (depending on your system) to install the necessary requirements:
```
pip install -r requirements_installer.txt
```

To run the actual installer use the following command:

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
- **SSH key directory**: path to the directory on the host that holds the SSH key pair used for git data-repository authentication

After this setup procedure the newly installed instance can be started via the commands provided by the installer.

### Initialization

The MAO installer provides an initialization sub-command that eases the setup of a newly installed instance. The `instance init` command queries the (if existing) federation and the MAO marketplace for tools and pipelines that a user might want to schedule on the new instance in order to participate actively in the federation.

Use the following command (as often as you want) to initialize or alter an instance and the pipelines that are scheduled on it:
```
python3 maoctl.py instance init
```

The `init` sub-command will list all pipelines available via the federation registry or the MAO marketplace and lets the user choose a schedule for the new pipeline if desired. The initial list will provided an overview of the pipelines along with a description, show if they are registered within the federation and show if they are already scheduled on the current instance (only possible on a subsequent execution of the `init` command).

```
Available MAO Pipelines ('✓'/'✗' indicate if pipline is already registered with this instance or federation):

[0] Dockerhub-Collector | registered on: this instance ✗, this federation ✓       # already registered within the federation, but not running on the current instance
        Description: 'Fetches metadata from DockerHub and analyses different KPIs for the discovered containers'
[1] Artifacthub-Collector | registered on: this instance ✗, this federation ✗     # not yet registered, fetched from marketplace
        Description: 'Fetches metadata from ArtifactHub and analyses different KPIs for the discovered artifacts'
```

After the pipeline selection the installers checks if all requirements are met on the current instance in order to run the pipeline properly. This includes the following checks:
- are all referenced tools available in the federation registry?
- are all referenced datasets available in the federation registry?

If a missing tool is discovered the installer offers the user the option to auto-register it, if the tool is available on the MAO marketplace.

If a dataset is discovered as missing the user has the option to add it as a local-only dataset that is not shared with other instances in the federation. This feature is particularly useful for new users or testing purposes as it allows a quick and rapid testing of different pipelines with a minimum setup effort. However if a dataset is missing that should be used in the whole federation the user should get in contact with the federation operator in order to get the corresponding dataset setup and registered for further usage in the federation.

As a last and optional step the user can enter a time rule to control the scheduled execution of each pipeline. This rule should be supplied in cron syntax (more information can be found e.g. [here](https://crontab.guru/)).

The steps after the pipeline selection are done for each of the previously selected pipelines individually.

After the `init` command is finished your newly installed MAO instances is up and running with the selected pipelines that if desired are scheduled for regular execution.

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
