from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import differ
import docker
import configparser
import etcd_client
import json
import base64
import glob
import os
import logging
import git
import subprocess
from datetime import datetime


docker_client = docker.from_env()
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


def schedule_run(data):
    #data = request.get_json()
    response = {}
    env = {}
    command = []
    renku = False
    container = data['container']
    response['container'] = container
    print(container)
    tool = data['tool']
    response['tool'] = tool
    print(tool)
    dataset = data['dataset']
    response['dataset'] = dataset
    print(dataset)
    if 'env' in data:
        env = data['env']
    if 'command' in data:
        command = data['command']
    if data['renku']:
        renku = True
    if data['cron']:
        freq = data['freq']
        if freq == 'daily':
            job = scheduler.add_job(run_container, 'interval', days=1,
                                    args=[container, command, env, tool, dataset, renku], id=tool,
                                    replace_existing=True,
                                    misfire_grace_time=64800, coalesce=True)
        elif freq == 'weekly':
            job = scheduler.add_job(run_container, 'interval', weeks=1,
                                    args=[container, command, env, tool, dataset, renku], id=tool,
                                    replace_existing=True,
                                    misfire_grace_time=64800, coalesce=True)
        else:
            job = scheduler.add_job(run_container, CronTrigger.from_crontab(freq),
                                    args=[container, command, env, tool, dataset, renku], id=tool,
                                    replace_existing=True,
                                    misfire_grace_time=64800, coalesce=True)
        response['job'] = job.id
        return response
    else:
        response['exec_result'] = run_container(container, command, env, tool, dataset, renku)
        return response


def run_container(container, command, env, tool, dataset, renku):
    result = {}
    status = ""
    if renku:
        datadir = f'{dataset}/data/input'
        docker_client.containers.run(container, command=command, environment=env,
                                 volumes={datadir: {'bind': '/usr/src/app/data'},
                                         '/var/run/docker.sock':
                                        {'bind': '/var/run/docker.sock'},
                                       '/usr/bin/docker':
                                        {'bind': '/usr/bin/docker'}},
                                 network='host')
        status = renku_update(dataset)
        return status
    else:
        docker_client.containers.run(container, command=command, environment=env,
                                 volumes={dataset: {'bind': '/usr/src/app/data'},
                                        '/var/run/docker.sock':
                                        {'bind': '/var/run/docker.sock'},
                                       '/usr/bin/docker':
                                        {'bind': '/usr/bin/docker'}},
                                 network='host')
        result = differ.detect(dataset, tool)
        return result


def renku_update(path):
    # Get the Renku project repo
    repo = git.Repo(path)
    cwd = os.getcwd()
    os.chdir(path)
    # Attempt a pull
    try:
        #origin = repo.remotes.origin
        #origin.pull()
        subprocess.run('git pull', shell=True)
    except:
        logging.info("Pull not completed")
        #os.chdir(cwd)
    # Commit and push new data
    try:
        #repo.git.add('.')
        #repo.git.commit(m="Auto: Data update")
        #repo.git.push()
        subprocess.run('git add .', shell=True)
        subprocess.run('git commit -m "Auto: Data update"', shell=True)
        subprocess.run('git push', shell=True)
    except:
        logging.error("Data update failed")
        #os.chdir(cwd)
        return "Error pushing data to Renku"
    # Run the renku workflow
    try:
        subprocess.run("renku -S update", shell=True)
    except:
        logging.error("Renku update failed")
        #os.chdir(cwd)
        return "Error running Renku workflow"
    # Push changes
    try:
        subprocess.run('git push', shell=True)
    except:
        logging.error("Final push failed")
        #os.chdir(cwd)
        return "Error pushing workflow result"
    os.chdir(cwd)
    return "Renku project successfully updated"



def listen():
    try:
        print(etcd_client.list('notifications'))
        logging.info(etcd_client.list('notifications'))
        # Send notifications as email
        # Delete notifications
    except:
        print("No notifications")
        logging.info("No notifications")

def list_jobs():
    job_list = scheduler.get_jobs()
    response = {}
    for item in job_list:
        response[item.id] = str(item.next_run_time)
    return response


def delete_job(id):
    scheduler.remove_job(id)
    return "Unscheduled " + id


if jobstore:
    scheduler.add_job(listen, 'interval', seconds=10, id = 'listen',
                      replace_existing=True,
                      misfire_grace_time=5, coalesce=True)
