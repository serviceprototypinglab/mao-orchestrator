import git
import datetime
import configparser
import requests
import json
import schedule
import shutil
import base64
import glob
from datetime import datetime
import logging
import os
import subprocess
from etcd_client import write, get
import collect

#logging.basicConfig(level=logging.DEBUG)
config = configparser.ConfigParser()
config.read('config.ini')
importdir = config['WORKING_ENVIRONMENT']['IMPORTDIR']

#### New pipeline: username is used to generate a name for the branch
user = config['WORKING_ENVIRONMENT']['USER']
if importdir.endswith('/'):
    importdir = importdir[:-1]


def list_jobs():
    return schedule.list_jobs()


def remove_job(id):
    return schedule.delete_job(id)


def sync(data):
    # Use new scheduler
    response = {}
    command = []
    env = {}
    renku = False
    blob = get('tools/{}'.format(data['name']))
    payload = json.loads(blob)
    if 'dataset' in data and 'node' in data:
        new_repo = get(f"data/{data['dataset']}/{data['node']}")
        payload['data_repo'] = new_repo
    tool = payload['image']
    print("Tool invoked: " + tool)
    response['tool'] = tool
    dataset = importdir + "/" + data['name']
    print("Data directory: " + dataset)
    response['datadir'] = dataset
    if 'env' in data:
        env = data['env']
    if 'command' in data:
        command = data['command']
    if 'renku' in data:
        renku = True
        #payload['data_repo'] = data['renku']
    # Check if dataset has been cloned already
    if not config.has_option('DATA_REPOS', data['name']):
        # Clone dataset
        print("Cloning dataset from: " + payload['data_repo'] + " to: " + dataset)
        response['dataset'] = payload['data_repo']
        print("Updating config")
        if not config.has_section('DATA_REPOS'):
            config.add_section('DATA_REPOS')
        config.set('DATA_REPOS', data['name'], dataset)
        with open('config.ini', 'w') as f:
            config.write(f)
        try:
            #git.Repo.clone_from(payload['data_repo'], dataset)
            subprocess.run(f"git clone {payload['data_repo']} {dataset}", shell=True)
        except:
            print("Error cloning data")
    if data['cron']:
        freq = data['frequency']
        json_out = {
            "container": tool,
            "tool": data['name'],
            "dataset": config['DATA_REPOS'][data['name']],
            "cron": data['cron'],
            "freq": freq,
            "command": command,
            "env": env,
            "renku": renku
        }
    else:
        json_out = {
            "container": tool,
            "tool": data['name'],
            "dataset": config['DATA_REPOS'][data['name']],
            "cron": data['cron'],
            "command": command,
            "env": env,
            "renku": renku
        }
    print("Message to scheduler: " + json.dumps(json_out))
    response['message'] = json.dumps(json_out)
    response['scheduler_output'] = schedule.schedule_run(json_out)
    return response

###### New pipeline methods ###################################################

# Attention!!! This code will not work in docker before adding ssh config
def pipeline_init(tool, dataset):
    # Clone dataset
    ## Get git link
    dataset_json = get(f"dataset/{dataset}")
    ## etcd does not like double quotes but json needs them
    dataset_json = dataset_json.replace("'", '"')
    dataset_dict = json.loads(dataset_json)
    dataset_git = dataset_dict['master']
    local_dir = importdir + "/" + tool
    try:
        subprocess.run(f"git clone {dataset_git} {local_dir}", shell=True)
    except:
        return f"Could not clone, check if {local_dir} exists and is not empty"
    # Create new branch (use node name from config)
    branch_name = user
    ## Get into the git dir
    old_wd = os.getcwd()
    os.chdir(local_dir)
    try:
        subprocess.run(f"git checkout -b {branch_name}", shell=True)
        subprocess.run(f"git push --set-upstream origin {branch_name}", shell=True)
    except:
        return f"Could not create branch, check if {branch_name} already exists"
    os.chdir(old_wd)
    # Register the branch
    dataset_dict['nodes'].append(branch_name)
    write(f"dataset/{dataset}", dataset_dict)
    # Save the association tool + branch on node (including local path)
    pipeline = {"tool": tool,
                "dataset": dataset,
                "branch": branch_name,
                "local_dir": local_dir
               }
    try:
        with open("pipelines.json", 'r') as pipeline_file:
            pipelines = json.load(pipeline_file)
    except:
        pipelines = {"pipelines": {}}
    with open("pipelines.json", 'w') as pipeline_file:
        pipelines['pipelines'][tool] = pipeline
        json.dump(pipelines, pipeline_file, indent=4)
    return pipeline

### Scheduling not supported yet
### Need tool for testing
def pipeline_run(name):
    # Read config
    with open("pipelines.json", 'r') as pipeline_file:
        pipelines = json.load(pipeline_file)
    pipeline = pipelines['pipelines'][name]
    local_dir = pipeline['local_dir']
    # Run the tool + Mount the branch folder
    ## Fetch tool metadata from registry
    tool_json = get(f"tools/{name}")
    ## etcd does not like double quotes but json needs them
    tool_json = tool_json.replace("'", '"')
    tool_dict = json.loads(tool_json)
    tool_image = tool_dict['image']
    ## Use NEW run method from scheduler
    schedule.pipeline_run(tool_image, local_dir)
    return pipeline

###### End of new pipeline methods ############################################



def list_local():
    response = {}
    for entry in config['DATA_REPOS']:
        response[entry] = config['DATA_REPOS'][entry]
    return response

def remove_local(name):
    shutil.rmtree(config['DATA_REPOS'][name])
    config.remove_option('DATA_REPOS',name)
    with open('config.ini', 'w') as f:
        config.write(f)
    return "Deleted {} from local filesystem".format(name)



def retrieve(name, node):
    try:
        value = get("/data/" + name + '/' + node)
    except:
        print("No such entry")
        return "This name does not correspond to an entry"
    try:
        #git.Repo.clone_from(value, importdir + "/" + name)
        subprocess.run(f"git clone {value} {importdir + '/' + name + '/' + node}", shell=True)
        if not config.has_option('DATA_REPOS', name):
            print("Updating config")
            logging.info("updating config")
            if not config.has_section('DATA_REPOS'):
                config.add_section('DATA_REPOS')
            config.set('DATA_REPOS', name, importdir + "/" + name)
            with open('config.ini', 'w') as f:
                config.write(f)
        return "Cloned: {} to {}".format(value, importdir + "/" + name)
    except:
        print("Error cloning data, trying to pull")
        logging.warning("Error cloning data, trying to pull")
    try:
        repo = git.Repo(importdir + "/" + name)
        o = repo.remotes.origin
        o.pull()
        if not config.has_option('DATA_REPOS', name):
            print("Updating config")
            if not config.has_section('DATA_REPOS'):
                config.add_section('DATA_REPOS')
            config.set('DATA_REPOS', name, importdir + "/" + name)
            with open('config.ini', 'w') as f:
                config.write(f)
        return "Pulled: {} to {}".format(value, importdir + "/" + name)
    except:
        print("Error pulling data.")
        logging.error("Error retrieving data.")
        return "Error pulling data."


def temp_retrieve(name, nodes):
    for node in nodes:
        try:
            value = get("/data/" + name + '/' + node)
        except:
            print("No such entry")
            return "This name does not correspond to an entry"
        try:
            #git.Repo.clone_from(value, importdir + "/" + name)
            subprocess.run(f"git clone {value} {importdir + '/' + 'tmp' + '/' + name + '/' + node}", shell=True)
        except:
            print("Error cloning data")
    collect.consensus(importdir + '/' + 'tmp' + '/' + name)
