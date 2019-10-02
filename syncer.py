import etcd
import git
import datetime
import configparser
import requests



config = configparser.ConfigParser()
config.read('config.ini')
importdir = config['WORKING_ENVIRONMENT']['IMPORTDIR']
etcd_host = config['ETCD']['HOST']
etcd_port = int(config['ETCD']['PORT'])
client = etcd.Client(host=etcd_host, port=etcd_port)


def write(key,value):
    client.set(key, value)


def list(key):
    directory = client.get(key)
    qresult = []
    for result in directory.children:
        qresult.append(result.key)
    return qresult


def get(key):
    return client.get(key).value


def sync(data):
    # Run tool
    #mao_runner.run_program(data)
    # Use new scheduler
    tool = client.get('tools/{}'.format(data['name'])).value
    dataset = data['dataset']
    freq = data['frequency']
    json = {
        "container": tool,
        "tool": data['name'],
        "dataset": dataset,
        "freq": freq
    }
    requests.post('http://127.0.0.1:5000/run', json=json)


    # Retrieve name and link to dataset from request
    # Push to dataset using git
    try:
        datalink = client.get(('/data/{}'.format(data['dataset']))).value
        print("This dataset is associated with this request:", datalink)
    except:
        print("Associated dataset not registered")
        return


def retrieve(name):
    try:
        value = client.get("/data/" + name).value
    except:
        print("No such entry")
        return
    try:
        git.Repo.clone_from(value, importdir + "/" + name)
    except:
        print("Error cloning data")
        return
