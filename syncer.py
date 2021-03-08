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
#import collect

#logging.basicConfig(level=logging.DEBUG)
config = configparser.ConfigParser()
config.read('config.ini')
importdir = config['WORKING_ENVIRONMENT']['IMPORTDIR']
hostdir = config['WORKING_ENVIRONMENT']['HOSTDIR']

#### New pipeline: username is used to generate a name for the branch
user = config['WORKING_ENVIRONMENT']['USER']
if importdir.endswith('/'):
    importdir = importdir[:-1]


def list_jobs():
    return schedule.list_jobs()


def remove_job(id):
    return schedule.delete_job(id)

###### New pipeline methods ###################################################

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
        with open(f"{importdir}/pipelines.json", 'r') as pipeline_file:
            pipelines = json.load(pipeline_file)
    except:
        pipelines = {"pipelines": {}}
    with open(f"{importdir}/pipelines.json", 'w') as pipeline_file:
        pipelines['pipelines'][tool] = pipeline
        json.dump(pipelines, pipeline_file, indent=4)
    return pipeline

### Scheduling not supported yet
def pipeline_run(name, cron):
    # Read config
    with open(f"{importdir}/pipelines.json", 'r') as pipeline_file:
        pipelines = json.load(pipeline_file)
    pipeline = pipelines['pipelines'][name]
    local_dir = pipeline['local_dir']
    host_dir = hostdir+ "/" + name
    # Run the tool + Mount the branch folder
    ## Fetch tool metadata from registry
    tool_json = get(f"tools/{name}")
    ## etcd does not like double quotes but json needs them
    tool_json = tool_json.replace("'", '"')
    tool_dict = json.loads(tool_json)
    tool_image = tool_dict['image']
    ## Use NEW run method from scheduler
    if cron == 'none':
        output = schedule.pipeline_run(tool_image, local_dir, host_dir)
        return {"pipeline": pipeline, "output": output}
    else:
        output = schedule.pipeline_cron(tool_image, local_dir, host_dir, cron)
        return {"pipeline": pipeline, "job_id": output}

###### End of new pipeline methods ############################################
