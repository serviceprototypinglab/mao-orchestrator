import etcd
import git
from github import Github
import datetime
import configparser
import requests
import json
import schedule


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
    response = {}
    blob = client.get('tools/{}'.format(data['name'])).value
    payload = json.loads(blob)
    tool = payload['image']
    print("Tool invoked: " + tool)
    response['tool'] = tool
    dataset = importdir + "/" + data['name']
    print("Data directory: " + dataset)
    response['datadir'] = dataset
    # Check if dataset has been cloned already
    if data['name'] not in config['DATA_REPOS']:
        # Clone dataset
        print("Cloning dataset from: " + payload['data_repo'] + " to: " + dataset)
        response['dataset'] = payload['data_repo']
        try:
            git.Repo.clone_from(payload['data_repo'], dataset)
            print("Updating config")
            config.set('DATA_REPOS', data['name'], dataset)
            with open('config.ini', 'w') as f:
                config.write(f)
        except:
            print("Error cloning data")
    if data['cron']:
        freq = data['frequency']
        json_out = {
            "container": tool,
            "tool": data['name'],
            "dataset": dataset,
            "cron": data['cron'],
            "freq": freq
        }
    else:
        json_out = {
            "container": tool,
            "tool": data['name'],
            "dataset": dataset,
            "cron": data['cron']
        }
    print("Message to scheduler: " + json.dumps(json_out))
    response['message'] = json.dumps(json_out)
    response['scheduler_output'] = schedule.schedule_run(json_out)
    return response


def retrieve(name):
    try:
        value = client.get("/data/" + name).value
    except:
        print("No such entry")
        return "This name does not correspond to an entry"
    try:
        git.Repo.clone_from(value, importdir + "/" + name)
        return "Cloned: {} to {}".format(value, importdir + "/" + name)
    except:
        print("Error cloning data")
        return "Error clonding data"
