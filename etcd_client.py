import configparser
import logging

import etcd

# logging.basicConfig(level=logging.DEBUG)
config = configparser.ConfigParser()
config.read("config.ini")
etcd_host = config["ETCD"]["HOST"]
etcd_port = int(config["ETCD"]["PORT"])
client = etcd.Client(host=etcd_host, port=etcd_port)


def write(key, value, ephemeral=False):
    if not ephemeral:
        client.set(key, value)
        logging.info(f"etcd key {key} has been set to {value}")
    else:
        client.set(key, value, ttl=60)
        logging.info(f"etcd key {key} has been set to {value} with a 60 TTL")


def list(key):
    qresult = []
    try:
        directory: etcd.EtcdResult = client.get(key)
        for result in directory.leaves:
            qresult.append(result.key)
    except etcd.EtcdKeyNotFound:
        return qresult

    return qresult


def get(key):
    return client.get(key).value


def delete(key):
    client.delete(key)
    return "Successfully deleted " + key


def delete_recursive(key):
    client.delete(key, recursive=True)
    return "Successfully deleted " + key


def read_recursive(key):
    directory = client.read(key, recursive=True)
    qresult = {}
    for result in directory.children:
        qresult[result.key] = result.value
    return qresult


def directory(key):
    return client.read(key, recursive=True)


def lock(id):
    lock = etcd.Lock(client, id)
    lock.acquire(
        blocking=True,  # will block until the lock is acquired
        lock_ttl=None,  # lock will live until we release it
        timeout=300,  # timeout for lock acquirement
    )
    return lock
