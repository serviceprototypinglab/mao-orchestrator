# Discovery

The MAO Gateway maintains a database of known MAO cluster members, and can talk to them to request a cluster reconfiguration. This allows it to remotely obtain the information needed for a new member to join the cluster.

The operator of the new node can then use this information to configure their etcd node to join the cluster.

## Limitations
The reconfiguration is performed at the request of the Gateway, but setting up etcd on the new node is left up to the operator, as how etcd is run (eg Docker or systemd) may vary, and etcd is troublesome to clean up if misconfigured.
## Warning
It is recommended to **not** use this feature on small clusters **(< 5 members)** as an erroneous configuration that results in loss of majority may cause the etcd cluster to enter a 'panic' state which is very hard to recover from.
