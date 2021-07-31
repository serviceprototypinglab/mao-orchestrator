# Pipelines

Pipelines are the execution unit of the MAO orchestrator framework. A pipeline is composed of several steps that are executed subsequently and some general metadata about the pipelines specifics.

The main purpose of a pipeline is the plumping between tools and datasets. Each pipeline step connects a single tool execution with a defined input dataset (optional) and an output dataset. Additionally the execution environment and configuration for each tool is stored alongside with each pipeline step.

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
python maoctl.py pipeline get --name <name>
```

### Registering new pipelines

The registration of a new pipeline can be conveniently be done via the MAO installer or via the API. A CLI for registering new pipelines is currently not available.

Details about the pipeline registration can be found in the projects main README which can be found [here](../README.md).