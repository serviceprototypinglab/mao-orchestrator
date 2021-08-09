# Voting

In a future version of MAO differing result sets from the instances within a federations shall be merged or agreed on trough a sophisticated consensus algorithm.

This document currently only describes the technical implementation of a federation wide voting lock which was introduced as a preliminary work for the final consensus module.

## etcd-based voting lock

The current version of MAO simply merges the current state of the instance branch onto the `ground-trough` branch that represents the federation wide agreed set of metrics.

This merge happens after each pipelines step execution. In order to prevent merge conflicts or concurrent "votes" each merge is executed with a lock on the specific output dataset.

These locks are federation wide and technically implemented by the locking feature of the `python-etcd` library. The locking key is derived from the dataset git URL and represented in etcd as base64 encoded value in the `_locks` directory.

Sample etcd locks:

```
/_locks/L2hvbWUvdXNlci9kYXRhL2JhcmVfbWFvLWRlbW8tZGF0YXNldA==
/_locks/L2hvbWUvdXNlci9kYXRhL2JhcmVfY2lwb2xpY2UtZGF0YXNldA==
/_locks/L2hvbWUvdXNlci9kYXRhL2JhcmVfZGMtdmFsaWRhdG9yLWlucHV0LWRhdGFzZXQ=
```

If a orphan lock is present in the system a federation operator can find the appropriate lock via decoding the key in the `_locks` directory:

```
echo "Z2l0QGdpdGh1Yi5jb206c2VydmljZXByb3RvdHlwaW5nbGFiL21hby1vcmNoZXN0cmF0b3IuZ2l0Cg==" | base64 -d
git@github.com:serviceprototypinglab/mao-orchestrator.git
```

And removing the lock by simply deleting the appropriate key from the `_locks` directory:

```
docker exec -it <mao-etcd-container> etcdctl rm /_locks/Z2l0QGdpdGh1Yi5jb206c2VydmljZXByb3RvdHlwaW5nbGFiL21hby1vcmNoZXN0cmF0b3IuZ2l0Cg==
```
