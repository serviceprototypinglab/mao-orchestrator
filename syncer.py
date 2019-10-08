import etcd
import git
from github import Github
import datetime
import configparser
import requests
import json


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
    # Use new scheduler
    blob = client.get('tools/{}'.format(data['name'])).value
    payload = json.loads(blob)
    tool = payload['image']
    print("Tool invoked: " + tool)
    dataset = importdir + "/" + data['name']
    print("Data directory: " + dataset)
    # Check if dataset has been cloned already
    if data['name'] not in config['DATA_REPOS']:
        # Clone dataset
        print("Cloning dataset from: " + payload['data_repo'] + " to: " + dataset)
        try:
            git.Repo.clone_from(payload['data_repo'], dataset)
            print("Updating config")
            config.set('DATA_REPOS', data['name'], dataset)
            with open('config.ini', 'w') as f:
                config.write(f)
        except:
            print("Error cloning data")
    freq = data['frequency']
    json_out = {
        "container": tool,
        "tool": data['name'],
        "dataset": dataset,
        "cron": data['cron'],
        "freq": freq
    }
    print("Message to scheduler: " + json.dumps(json_out))
    requests.post('http://127.0.0.1:5000/run', json=json_out)
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
