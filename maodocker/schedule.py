from apscheduler.schedulers.asyncio import AsyncIOScheduler
import differ
import docker
import configparser
import etcd
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
etcd_host = config['ETCD']['HOST']
etcd_port = int(config['ETCD']['PORT'])
client = etcd.Client(host=etcd_host, port=etcd_port)
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
                                 network='mao')
    result = differ.detect(dataset, tool)
    insights.report(dataset, tool, config['WORKING_ENVIRONMENT']['user'])
    return result


def listen():
    try:
        directory = client.get('notifications')
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
        directory = client.read('raw', recursive=True)
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
    with open('known_audits.json', 'r') as archive:
        known_audits = json.load(archive)
        print(known_audits)
    keys_to_delete = []
    for key in known_audits:
        audit_time = datetime.strptime(known_audits[key], "%Y-%m-%d %H:%M:%S.%f")
        print(audit_time)
        delta = datetime.now() - audit_time
        print(delta)
        if (delta.total_seconds() // 60) % 60 > 10:
            keys_to_delete.append(key)
    for key in keys_to_delete:
        print("Deleting ", key)
        del known_audits[key]
    with open('known_audits.json', 'w') as archive:
        json.dump(known_audits, archive)
    try:
        # get all audits
        directory = client.get('audit')
        audits = {}
        for result in directory.children:
            audits[result.key] = result.value
        for key in audits:
            details = json.loads(audits[key])
            print(details)
            print(config['WORKING_ENVIRONMENT']['user'])
            # check if self is the issuer
            if details['issuer'] == config['WORKING_ENVIRONMENT']['user']:
                # check if 10 minutes have passed
                audit_time = datetime.strptime(details['timestamp'], "%Y-%m-%d %H:%M:%S.%f")
                delta = datetime.now() - audit_time
                if (delta.total_seconds() // 60) % 60 > 10:
                    #if yes, get files, validate, announce leader, delete entries
                    #make temp folder IF not exists
                    if not os.path.isdir(config['WORKING_ENVIRONMENT']['auditdir'] + '/' + key.split('/')[2]):
                        os.mkdir(config['WORKING_ENVIRONMENT']['auditdir'] + '/' + key.split('/')[2])
                    #get csv entries for this audit
                    files = client.get('csv/{}'.format(key.split('/')[2]))
                    csvs = {}
                    # retrieve encoded csvs
                    for result in files.children:
                        csvs[result.key] = result.value
                    # decode csvs
                    for key, value in csvs.items():
                        payload = json.loads(value)
                        encoded = payload['payload'][2:-1].encode('latin1')
                        decoded = base64.b64decode(encoded)
                        with open(config['WORKING_ENVIRONMENT']['auditdir'] + '/' + key.split('/')[2] + '/' + key.split('/')[3] + '.csv', 'wb') as output:
                            output.write(decoded)
                    #perform validation
                    winner = audit.audit(config['WORKING_ENVIRONMENT']['auditdir'] + '/' + key.split('/')[2])
                    #announce leader
                    print('##########################')
                    print(key.split('/')[2])
                    print(details['tool'])
                    print(details['timestamp'])
                    print(str(winner))
                    client.set("winners/{}".format(key.split('/')[2]), '{{"tool":"{}",\
                    "timestamp":"{}",\
                    "winner":"{}"}}'.format(details['tool'], details['timestamp'], str(winner)))
                    #delete audit, csvs and temp files
                    client.delete("/csv/{}".format(key.split('/')[2]), recursive=True)
                    client.delete("/audit/{}".format(key.split('/')[2]), recursive=True)
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
                        # find most recent csv
                        path = config['DATA_REPOS'][details['tool']]
                        filenames = glob.glob("{}/*.csv".format(path))
                        filenames.sort()
                        # filenames[-1] is the latest file
                        # if they are named appropriately
                        with open(filenames[-1], 'rb') as f:
                            encoded = base64.b64encode(f.read())
                        # write entry with encoded payload
                        client.set("csv/{}/{}".format(key.split('/')[2], config['WORKING_ENVIRONMENT']['user']), '{{"tool":"{}",\
                        "timestamp":"{}",\
                        "payload":"{}"}}'.format(details['tool'], datetime.now(), encoded))
                        print("Contributed {} to {}".format(filenames[-1], key))
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
