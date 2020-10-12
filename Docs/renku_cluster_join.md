# Joining an existing MAO cluster

The steps for joining an existing cluster are similar to the initial setup, with the exception of the etcd parameters which need to be exchanged as in the [etcd runtime reconfiguration guide.](https://etcd.io/docs/v3.3.12/op-guide/runtime-configuration/)

In brief, you need to inform the operator of an existing node of your desired username and the public IP of your server, and they will respond with the parameters you need to change in this part of the compose file:

```yaml
- ETCD_INITIAL_CLUSTER_TOKEN=etcd-cluster
- ETCD_INITIAL_CLUSTER=<names and IPs of nodes>
- ETCD_INITIAL_CLUSTER_STATE=existing
```

The rest of the proceedure is identical.
