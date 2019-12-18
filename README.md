# MAO Orchestrator

Distributed orchestrator for the [MAO-MAO collaborative research](https://mao-mao-research.github.io/) framework. Allows scheduled execution of periodic data collectors and has built-in spike detection for the data.
This implementation makes use of an etcd cluster for member discovery and metadata sharing and a simple git interface for cloning data sets.
## Contents
- [Install instructions](#install-instructions) To setup the orchestrator
- [Docker-Compose](#docker-compose) An easier alternative to setting it up manually (WIP)
- [MAOCTL](#maoctl) To interact with the running instance
- [MAO- Gateway](mao-gateway) A tool that allows external tools to communicate with the cluster (WIP)
- [Tool compliance](#tool-compliance) To create tools that can be deployed to the orchestrator

# Install instructions

## etcd
- Install etcd.
```
sudo apt install etcd-server etcd-client
```

etcd creates a system service upon installation that provides a local single node cluster. To join the existing cluster you would have to contact us to add your server and come back to you with the necessary parameters, which need to be added to the execution parameters of the `etcd.service` file. An intermediate service automating some of these steps will be set up in the future, but modifying the service file will remain manual for safety.

It is possible to use a single-node configuration. While usable, it will not give access to the distributed nature of the system, ie the tools and datasets registered by other collaborators.
- **etcd uses port 2380 for peer-to-peer communication** so ensure it is accessible both for ingress and egress.
- If you need to access etcd externally you will need **port 2379 (for etcd client communication)** to be accessible to ingress as well. This may be useful for debugging purposes or if you wish to install the Orchestrator on a different system from your etcd node.

## Orchestrator configuration
- Setup your importdir and etcd settings in config.ini . Importdir is where your local data will be stored. The DATA_REPOS entries are auto-generated when a tool is run for the first time. You can delete the sample entry.
- `pip3 install -r requirements.txt`

**NOTE:** The scheduler will not run on Python versions prior to 3.5

## Job Persistence (optional)

The registry of tools and datasets is always available to you as long as the etcd cluster is running. However job persistence within your instance is optional. To use it, you need to configure a persistent job store using the instructions below. If you do not wish to use this feature you can skip to the next section.

- **Install PostgreSQL**

```
sudo apt install postgresql postgresql-contrib libpq-dev
pip3 install psycopg2
```

- **Setup the Job Store database**
For this example we will create a database called "schedule" owned by a user named "scheduler" with the password "password".
  - Login to psql as the postgres user:
  ```
   sudo -i -u postgres psql
  ```
  - Create the user and database:
  ```
  drop user if exists scheduler;
  create user scheduler with password 'password';
  alter user scheduler createdb;
  create database schedule;
  grant all privileges on database schedule to scheduler;
  ```
  - Now you can log on to the Job Store as the "scheduler" user if you need to:
  ```
  psql -U scheduler -h localhost -d schedule
  ```
  You should check this once after running the orchestrator for the first time. Since the notification listener job is started immediately, you should see at least once record in the job table in this database.
- **Fill in the connection details in config.ini**
```
[POSTGRES]
user = scheduler
password = password
db = schedule
```

**Note:** If this section is not filled the scheduler will store the jobs in memory, and lose them when it quits.

## Starting the orchestrator:
To launch the orchestrator:
```
python3 async_launcher.py
```
By default it runs in the foreground so you will need a new terminal.

# Docker-Compose
You can also set up the orchestrator with Docker Compose. This option is still at a very early stage and is not considered stable enough for working with the current 'production' cluster, but is a much quicker way of testing and demonstrating the system.

Before bringing up the compose, create a Docker network to house the application. This will allow the tools managed by the orchestrator to connect to the same network:
```
docker network create mao --driver bridge
```
Then you can bring up the orchestrator:
```
docker-compose up
```
As this is an early implementation for testing purposes, the configuration parameters for etcd and the orchestrator are hardcoded into the `docker-compose.yml` configuration file. Any changes need to be made there directly.

# MAOCTL

The command-line client for the orchestrator can be used for either the native or docker-compose version to interact and issue commands to the orchestrator.
Use:
```
python3 maoctl.py --help
```
to begin.

# MAO - Gateway
This experimental tool is meant to enable external tools to interact with the data in the cluster. It allows external sources to read all entries of the etcd cluster, and also allows them to write short-lived 'raw' entries. Raw entries are picked up by a listener managed by the orchestrator and saved to datasets determined by their key values. The datasets are persistent but the entries themselves have a TTL of 60 seconds.

The gateway uses a database to save the IPs of current nodes in the cluster. It also has a discovery endpoint for joining the cluster, but that is disabled for the time being, as adding a misconfigured node to a small etcd cluster can cause a catastrophic failure.

- Set up the DB:
```
sh schema.sh
```
- Make changes to `session.ini` as needed. As the discovery service is not functional, you have to insert the first node into the database manually.
- Finally, launch the gateway:
```
python3 gateway.py
```

# Tool Compliance
To create tools that can be deployed to the MAO Orchestrator they need to comply with the following guidelines:
- Must be dockerized
- Must be able to launch with no interaction (the possibility to pass command line arguments may be added in a future update)
- Must put their generated data files in the `/usr/src/app/data` folder, as this is the folder mounted to the container.
- Though this is not enforced, it is recommended that output files are generated in such a way that subsequent runs do not overwrite the data generated previously.
- Must generate (in the same folder) a file named `control-<value>.csv` with each execution, where `value` should be sortable (for example the current date), in order for the spike detection to work. The file must contain a single numeric value (the control metric).
- Optionally, the tool can create an `insights.json` file in the same data directory. The file needs to be small and should be limited to useful key insights. The contents of the file are written to etcd directly to become accessible to external tools.

## The demo tool
The demo tool creates 3 mock data samples to trigger the spike detection and also shows the basic way to create a compliant tool. You can build it with Docker and register it (with a Github repository for the data, you can use any repository since after cloning it will only add data locally not make any commits) to test the functionality of the orchestrator.
