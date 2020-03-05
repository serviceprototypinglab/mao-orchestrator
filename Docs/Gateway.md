# The MAO Gateway

It became apparent that the tools of the MAO project where not all cron-jobs in need of modernization. Several more dynamic tools such as linters and benchmarks have been developed over the course of the project, and asking a developer to deploy a whole MAO instance to use them is impractical.

Thus it was conceived to allow these external tools (which anyway are the ones more relevant to developers directly) to 'phone home' and talk to the MAO federation. Not only does this allow them to send data to MAO and augment our datasets, it also conceivably allows them to read data from MAO to augment their own capabilities.

And so, the need for the MAO Gateway arose. This introduced a further complication to the current architecture:

MAO handles all of its data as files, thus 'talking' to MAO does not really give much access to the data.

The Gateway is designed to solve these issues by exposing the cluster as a service that can be communicated with conventionally. For this purpose it provides:

- Discovery, to allow new nodes to join the cluster and record existing nodes.

- The ability to read data from specific etcd directories, and write to them. This is augmented by the insights system, explained in the 'external data sources' page.

In the future, it will be possible to geo-replicate the gateway, as all nodes know each other, so a new gateway can be spun up by querying the cluster for members, if it knows at least one of them.
