# Peer-based data validation

When a tool is deployed by multiple cluster members, each will produce a data snapshot with each run. In the case of monitoring public repositories, these snapshots are expected to be identical, if run close enough together.

However, with certain data and web crawlers, unexpected errors may occur during data collection. This is easy to diagnose if a complete outage causes a snapshot to be missing, and was part of the motivation of the MAO geo-distributed infrastructure.

It becomes a bigger issue, if the crawler does not outright fail, but rather fails part of the requests it makes, producing invalid or corrupt entries. This is commonly observed in web-crawlers.

The peer-based validation system assists in discovering corrupt snapshots by choosing the best snapshot available out of all the members in the cluster.

**Important**: This does not mean the snapshot will not contain errors, and it is possible one of the 'bad' snapshots will contain information not available to the 'good' snapshots. This toolset is meant to assist, not replace common sense.

## Validation methodology

The method is based on two phases: aggregation of candidate snapshots and choosing the best snapshot.

### Aggregation of candidates

A cluster member can use the `audit` CLI command to initiate an audit on a specific dataset. This will trigger the process to begin.

- An `audit` entry will be written to etcd, detectable by each member's audit listener (an automatic job spawned by the orchestrator as it initializes). The audit entry also lists the auditor and the time the audit started.
- The auditor will submit its snapshot, if it has one. Files are Base64 encoded and submitted as short-lived etcd entries.
- Each member will submit its file if it has one. Members have a `known audits` file to prevent them from answering the same audit twice. This file get cleaned up periodically.
- After 10 minutes, the auditor will collect and decode the files, to begin the validation step. At this stage the audit and temp etcd etnries are cleaned up.

### Validation

The files are all compared to each other and assigned a 'strangeness' index. This index represents the number of unique entries in the file. If a single file has the smallest strangeness, it is declared the winner and announced via an etcd entry.

In the case of a draw, the files that are drawn are then compare to each other. If they are identical, they all get declared winners. If not, the draw is reported so that they can be examined manually.

## Limitations

The rationale is that valid entries will be identical and corrupt entries will be unique. This can only be applied to aggregated files, with one entry added per day, as files generated in one run are more unpredictable.

Finer differences are still impossible to detect with this method, especially differences in numeric values. The only cases where this will resolve conflicts reliably, with no human intervention, is where all valid files are expected to be completely identical, thus using this validation to select the 'odd ones out'.
