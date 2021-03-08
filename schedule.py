from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
#import docker
import configparser
import etcd_client
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


Path("./infile").mkdir(parents=True, exist_ok=True)
#docker_client = docker.from_env()
config = configparser.ConfigParser()
config.read('config.ini')
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
def pipeline_run(image, local_dir, host_dir):
    json_out = {
    "image": image,
    "data_dir": host_dir
    }
    r = requests.post('http://0.0.0.0:8081/run', json=json_out)
    print(r.json())
    old_wd = os.getcwd()
    os.chdir(local_dir)
    subprocess.run(f"git add .", shell=True)
    subprocess.run(f'git commit -m "auto-exec"', shell=True)
    subprocess.run(f"git push", shell=True)
    os.chdir(old_wd)
    return r.json()

def pipeline_cron(image, local_dir, host_dir, cron):
    job = scheduler.add_job(pipeline_run, CronTrigger.from_crontab(cron),
                            args=[image, local_dir, host_dir], id=image,
                            replace_existing=True,
                            misfire_grace_time=64800, coalesce=True)
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
