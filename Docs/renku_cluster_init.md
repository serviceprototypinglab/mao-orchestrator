# Initialisation of MAO cluster

## Server setup

It is recommended that servers and VMs that will run the system have at least **2 vCPUs and 4GB of RAM**. Storage as needed. For basic functionality only **port 2380** needs to be open to incoming traffic, as it is used in peer-to-peer communication.

## Renku integated setup

### Bakcend components

For the Renku integrated version of MAO, only the backend components will be launched as Docker containers, as Renku CLI and git commands need to run on the host. The docker-compose-nomao.yml file is created for this reason.

- Change the volume mount fields if necessary to map to your host directory structure.

- Set up the etcd parameters. The default values will work for a single node setup but the following parameters need to be set if bootstrapping a new cluster.

```yaml
- ETCD_NAME=<node-name>
# Make sure this matches the volume
- DATA-DIR=/etcd-data
# Endpoint the peers in the cluster will use to talk to this node
- ETCD_INITIAL_ADVERTISE_PEER_URLS=http://<public-ip>:2380
# Endpoint this node is listening at for peer requests
- ETCD_LISTEN_PEER_URLS=http://0.0.0.0:2380
# Endpoint this node is listening at for client requests
- ETCD_LISTEN_CLIENT_URLS=http://0.0.0.0:2379
# Endpoint clients can use to talk to this node
- ETCD_ADVERTISE_CLIENT_URLS=http://<public-ip>:2379
# The settings below need to be retrieved from an existing node
# to join an existing cluster
- ETCD_INITIAL_CLUSTER_TOKEN=etcd-cluster
- ETCD_INITIAL_CLUSTER=<node-name>=http://<public-ip>:2380
- ETCD_INITIAL_CLUSTER_STATE=new
```
Replace <public-ip> with your server's public IP and <node-name> with your desired node name.

### Orchestrator

Install the requirements for the orchestrator with
```
pip install -r requirements.txt
```

See the [github readme](https://github.com/serviceprototypinglab/mao-orchestrator) for troubleshooting.

Afterwards you can start the orchestrator service with
```
python async-launcher.py
```
See the readme and documentation for details on how to interact with the instance.

You can use existing OS utilities (like systemd unit files on systems that support it) to ensure the service starts automatically with the server but that is beyond the scope of this document.

### Renku

Ensure Renku is set up on the host and that you have created the necessary SSH keys, as the automation will be pushing data files to Renku on your behalf.
