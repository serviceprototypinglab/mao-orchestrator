from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
#import docker
import configparser
import json
import base64
import glob
import os
import logging
import git
import subprocess
import requests
from datetime import datetime
import yaml
from pathlib import Path
import tempfile
from etcd_client import get


EXECUTOR_URL = "http://0.0.0.0:8081/run"

Path("./infile").mkdir(parents=True, exist_ok=True)
#docker_client = docker.from_env()
config = configparser.ConfigParser()
config.read('config.ini')
importdir = config['WORKING_ENVIRONMENT']['IMPORTDIR']
scheduler = AsyncIOScheduler()
scheduler.add_executor('processpool')
jobstore = False
if config.has_section('POSTGRES') and config['POSTGRES']['DB'] != '':
    postgres_user = config['POSTGRES']['USER']
    postgres_pass = config['POSTGRES']['PASSWORD']
    postgres_db = config['POSTGRES']['DB']
    postgres_host = config['POSTGRES']['HOST']
    url = 'postgresql://{}:{}@{}/{}'.format(postgres_user, postgres_pass,
                                                   postgres_host, postgres_db)
    scheduler.add_jobstore('sqlalchemy', url=url)
    jobstore = True
#logging.basicConfig(level=logging.DEBUG)
#logging.getLogger('apscheduler').setLevel(logging.DEBUG)
scheduler.start()

"""
def run_container(container, command, env, tool, dataset):
    result = {}
    status = ""
    docker_client.containers.run(container, command=command, environment=env,
                             volumes={dataset: {'bind': '/usr/src/app/data'},
                                    '/var/run/docker.sock':
                                    {'bind': '/var/run/docker.sock'},
                                   '/usr/bin/docker':
                                    {'bind': '/usr/bin/docker'}},
                             network='host')
    return "done"
"""
##### New pipeline method #####################################################

def create_tmp_from_branch(repo_path, branch):
    '''Creates a temporary copy of the input data branch'''
    tmp = tempfile.TemporaryDirectory(dir=importdir)
    old_wd = os.getcwd()
    os.chdir(repo_path)
    try:
        # checkout branch
        subprocess.run(f"git checkout {branch}", shell=True)
        # copy content to tmp location
        subprocess.run(f"cp -rp {repo_path}/* {tmp.name}", shell=True)
    except:
        return f"Could not checkout {branch}, check status of git repo at {repo_path}"
    os.chdir(old_wd)
    return tmp

def git_checkout_branch(repo_path, branch):
    '''Perform checkout of given branch on repo'''
    old_wd = os.getcwd()
    os.chdir(repo_path)
    try:
        # checkout branch
        subprocess.run(f"git checkout -B {branch}", shell=True)
    except:
        return f"Could not checkout {branch}, check status of git repo at {repo_path}"
    os.chdir(old_wd)

def git_commit_push_branch(repo_path):
    '''Perform commit + push operation on given repo'''
    old_wd = os.getcwd()
    os.chdir(repo_path)
    try:
        subprocess.run(f"git add .", shell=True)
        subprocess.run(f'git commit -m "pipeline-exec"', shell=True)
        subprocess.run(f"git push", shell=True)
    except:
        return f"Could not commit + push, check status of git repo at {repo_path}"
    os.chdir(old_wd)

def voting_mock(repo_path, dataset):
    '''This is a voting mock that copies node branch to ground-truth'''
    old_wd = os.getcwd()
    os.chdir(repo_path)
    try:
        git_checkout_branch(repo_path, 'ground-truth')
        subprocess.run(f"git push --set-upstream origin ground-truth", shell=True)
        subprocess.run(f"git merge {dataset['branch']}", shell=True)
        subprocess.run(f'git commit -m "voting"', shell=True)
        subprocess.run(f"git push", shell=True)
    except:
        return f"Could not commit + push, check status of git repo at {repo_path}"
    os.chdir(old_wd)

def get_tool_image(tool_name):
    '''Retrieves tool image from federation'''
    tool_json = get(f"tools/{tool_name}")
    ## etcd does not like double quotes but json needs them
    tool_json = tool_json.replace("'", '"')
    tool_dict = json.loads(tool_json)
    return tool_dict['image']


def pipeline_run(importdir, hostdir, steps):
    '''Runs pipeline steps using remote executor'''
    
    for step in steps:
        # prepare datasets
        input_dataset = step['input_dataset']
        input_copy = None
        input_copy_path = None
        if input_dataset is not None:
            input_copy = create_tmp_from_branch(f"{importdir}/{input_dataset['name']}", 'ground-truth')
            input_copy_path = input_copy.name.replace(importdir, hostdir)
        git_checkout_branch(f"{importdir}/{step['output_dataset']['name']}", step['output_dataset']['branch'])

        exec_json = {
            "image": get_tool_image(step['tool']),
            "input_dir": input_copy_path,
            "output_dir": f"{hostdir}/{step['output_dataset']['name']}",
            "env": step['env'],
            "cmd": step['cmd'],
            "docker_socket": step['docker_socket']
        }

        # execute step via remote executor
        r = requests.post(EXECUTOR_URL, json=exec_json)

        # push output result + cleanup
        git_commit_push_branch(f"{importdir}/{step['output_dataset']['name']}")
        if input_copy is not None:
            input_copy.cleanup()

        voting_mock(f"{importdir}/{step['output_dataset']['name']}", step['output_dataset'])

def pipeline_cron(name, importdir, hostdir, steps, cron):
    job = scheduler.add_job(
        pipeline_run,
        CronTrigger.from_crontab(cron),
        args=[importdir, hostdir, steps],
        id=name,
        replace_existing=True,
        misfire_grace_time=64800,
        coalesce=True
        )
    return job.id

###############################################################################


def list_jobs():
    job_list = scheduler.get_jobs()
    response = {}
    for item in job_list:
        response[item.id] = str(item.next_run_time)
    return response


def delete_job(id):
    scheduler.remove_job(id)
    return "Unscheduled " + id
