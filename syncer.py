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
import audit
import logging
import os
import subprocess
from etcd_client import write, get

#logging.basicConfig(level=logging.DEBUG)
config = configparser.ConfigParser()
config.read('config.ini')
importdir = config['WORKING_ENVIRONMENT']['IMPORTDIR']
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



def retrieve(name):
    try:
        value = get("/data/" + name)
    except:
        print("No such entry")
        return "This name does not correspond to an entry"
    try:
        git.Repo.clone_from(value, importdir + "/" + name)
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


def create_audit(tool):
    # Creation of audit entry
    issuer = config['WORKING_ENVIRONMENT']['user']
    timestamp = datetime.now()
    audit_id = timestamp.microsecond
    write("audit/{}".format(audit_id), '{{"issuer":"{}",\
    "tool":"{}",\
    "timestamp":"{}"}}'.format(issuer, tool, timestamp))
    # Send file if exists
    if config.has_option('DATA_REPOS', tool):
        filename = audit.submit(tool, audit_id, issuer)
        return "Created audit {} and submitted file {}".format(audit_id, filename)
    else:
        return "Created audit {}. No local file to submit.".format(audit_id)
