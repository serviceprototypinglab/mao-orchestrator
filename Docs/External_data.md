# External Data Sources

The MAO Gateway allows tools to read from and write to specific etcd directories.

# Writing to etcd

Using the ` POST /write` endpoint of the gateway, the user can write a key/value pair to etcd. This gets written to the `/raw` directory within etcd. Raw entries have a TTL of 60 seconds.

A 'data listener' is spawned when the Orchestrator initializes that picks up raw entries every 10 seconds and saves them as JSON files.

# Insights aka Reading from etcd

If a MAO member wishes to develop a smart toolset, that augments an external tool with data from an internal tool, they can use the insights system.

An internal MAO tool can optionally write an `insights.json` file. After each execution, the scheduler will check if this file exists and write its contents to etcd's `/insights` directory, under the name of the tool. Then it can be accessed using the `GET /read` endpoint of the gateway.

To search for the right insight file, the Gateway also has the `GET /inspect` endpoint, which reads etcd directories recursively. 
