from apscheduler.schedulers.asyncio import AsyncIOScheduler
import differ
import docker
import configparser
import etcd_client
import audit
import json
import base64
import glob
import os
import insights
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
scheduler.start()


def schedule_run(data):
    #data = request.get_json()
    response = {}
    container = data['container']
    response['container'] = container
    print(container)
    tool = data['tool']
    response['tool'] = tool
    print(tool)
    dataset = data['dataset']
    response['dataset'] = dataset
    print(dataset)
    if data['cron']:
        freq = data['freq']
        if freq == 'daily':
            job = scheduler.add_job(run_container, 'interval', days=1,
                                    args=[container, tool, dataset], id=tool,
                                    replace_existing=True,
                                    misfire_grace_time=3600, coalesce=True)
        elif freq == 'weekly':
            job = scheduler.add_job(run_container, 'interval', weeks=1,
                                    args=[container, tool, dataset], id=tool,
                                    replace_existing=True,
                                    misfire_grace_time=3600, coalesce=True)
        response['job'] = job.id
        return response
    else:
        response['exec_result'] = run_container(container, tool, dataset)
        return response


def run_container(container, tool, dataset):
    result = {}
    docker_client.containers.run(container,
                                 volumes={dataset: {'bind': '/usr/src/app/data'}},
                                 network='host')
    result = differ.detect(dataset, tool)
    insights.report(dataset, tool, config['WORKING_ENVIRONMENT']['user'])
    return result


def listen():
    try:
        directory = etcd_client.get('notifications')
        qresult = {}
        for result in directory.children:
            qresult[result.key] = result.value
        print(qresult)
        # Send notifications as email
        # Delete notifications
    except etcd.EtcdKeyNotFound:

        print("No notifications")


def data_listen():
    try:
        directory = etcd_client.read_recursive('raw')
        qresult = {}
        for result in directory.children:
            qresult[result.key] = result.value
        print(qresult)
        for key, value in qresult.items():
            dir = config['WORKING_ENVIRONMENT']['importdir'] + '/' + key.split('/')[2]
            filename = dir + '/' + key.split('/')[3] + '.json'
            print(filename)
            print(value)
            if not os.path.isdir(dir):
                os.mkdir(dir)
            with open(filename, 'w') as output:
                output.write(value)
    except etcd.EtcdKeyNotFound:
        print("No pernding data")


def audit_listen():
    # delete known audits entries older than 10 minutes
    known_audits = audit.cleanup()
    try:
        # get all audits
        directory = etcd_client.get('audit')
        audits = {}
        current_user = config['WORKING_ENVIRONMENT']['user']
        for result in directory.children:
            audits[result.key] = result.value
        for key in audits:
            audit_id = key.split('/')[2]
            details = json.loads(audits[key])
            print(details)
            print(current_user)
            # check if self is the issuer
            if details['issuer'] == current_user:
                # check if 10 minutes have passed
                audit_time = datetime.strptime(details['timestamp'], "%Y-%m-%d %H:%M:%S.%f")
                delta = datetime.now() - audit_time
                if (delta.total_seconds() // 60) % 60 > 10:
                    #if yes, get files, validate, announce leader, delete entries
                    audit.validate(details, audit_id)
                else:
                    #if not, wait
                    pass
            else:
                if key in known_audits:
                    pass
                else:
                    known_audits[key] = str(datetime.now())
                    with open('known_audits.json', 'w') as archive:
                        json.dump(known_audits, archive)
                    # send file and save id to known audits
                    if config.has_option('DATA_REPOS', details['tool']):
                        filename = audit.submit(details['tool'], audit_id, current_user)
                        print("Contributed {} to {}".format(filename, key))
    except etcd.EtcdKeyNotFound:
        print("No on-going audits")


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
    scheduler.add_job(data_listen, 'interval', seconds=10, id = 'data_listen',
                      replace_existing=True,
                      misfire_grace_time=5, coalesce=True)
    scheduler.add_job(audit_listen, 'interval', seconds=10, id = 'audit_listen',
                      replace_existing=True,
                      misfire_grace_time=5, coalesce=True)
