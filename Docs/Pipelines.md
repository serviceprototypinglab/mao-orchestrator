# Pipelines

Pipelines are the execution unit of the MAO orchestrator framework. A pipeline is composed of several steps that are executed subsequently per node (e.g. metrics acquisition, aggregation, ...) and some general metadata about the pipelines specifics.

The main purpose of a pipeline is the plumping between tools and datasets. Each pipeline step connects a single tool execution with a defined input dataset (optional) and an output dataset. Additionally the execution environment and configuration for each tool is stored alongside with each pipeline step.

Ground truth [voting](Voting.md) takes place on the resulting datasets for all federations spanning multiple nodes.

## The pipeline registry

The pipeline registry stores information in the federation wide etcd cluster as well as in the instance local PostgreSQL database.

- `Global` etcd: currently only stores the pipeline names that run on at least one instance within the federation
  - etcd path `/pipelines/<pipeline-name>`
- `Local` PostgreSQL: stores the detailed pipeline configuration for its specific instance (details: [here](Postgresql.md))

### Getting information

You can list the available pipelines or get detailed information on a specific pipeline.

#### CLI

List all instance registered pipelines:
```
python maoctl.py pipeline get
```

Get detailed information about a single pipeline:
```
python maoctl.py pipeline get --name NAME
```

### Registering new pipelines

The registration of a new pipeline can be conveniently be done via the MAO installer, via the API or through the CLI.

#### CLI

Enter the promt for creating a new pipeline
```
python maoctl.py pipeline add
```
The CLI will follow through several steps where you can provide the necessary information regarding the pipeline

Details about the pipeline registration can be found in the projects main README which can be found [here](../README.md).
