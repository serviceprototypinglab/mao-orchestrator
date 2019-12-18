import etcd
import configparser


config = configparser.ConfigParser()
config.read('config.ini')
etcd_host = config['ETCD']['HOST']
etcd_port = int(config['ETCD']['PORT'])
client = etcd.Client(host=etcd_host, port=etcd_port)


def write(key, value, ephemeral=False):
    if not ephemeral:
        client.set(key, value)
    else:
        client.set(key, value, ttl=60)


def list(key):
    directory = client.get(key)
    qresult = []
    for result in directory.children:
        qresult.append(result.key)
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
    return client.read(key, recursive=True)
