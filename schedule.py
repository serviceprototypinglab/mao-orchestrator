from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler
import differ
import docker
import configparser
import etcd


schedule = Flask(__name__)
client = docker.from_env()
config = configparser.ConfigParser()
config.read('config.ini')
importdir = config['WORKING_ENVIRONMENT']['IMPORTDIR']
etcd_host = config['ETCD']['HOST']
etcd_port = int(config['ETCD']['PORT'])
client = etcd.Client(host=etcd_host, port=etcd_port)
scheduler = BackgroundScheduler()
scheduler.start()


@schedule.route('/run', methods=['POST'])
def schedule_run():
    data = request.get_json()
    container = data.get('container')
    tool = data.get('tool')
    dataset = data.get('dataset')
    if data.get('cron')==True:
        freq = data.get('freq')
        if freq == 'daily':
            job = scheduler.add_job(run_container, 'interval', days=1,
                                    args=[container, tool, dataset],
                                    misfire_grace_time=None, coalesce=True)
        elif freq == 'weekly':
            job = scheduler.add_job(run_container, 'interval', weeks=1,
                                    args=[container, tool, dataset],
                                    misfire_grace_time=None, coalesce=True)
        return "job details: %s" % job
    else:
        run_container(container, tool, dataset)
        return "ran"


def run_container(container, tool, dataset):
    client.containers.run(container,
                          volumes={'{}/{}'.format(importdir, tool):
                                   {'bind': '/usr/src/app/data'}})
    differ.detect('{}/{}'.format(importdir, tool), dataset)

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

        print ("No notifications")


scheduler.add_job(listen, 'interval', seconds=10,
                        misfire_grace_time=None, coalesce=True)


if __name__ == '__main__':
    schedule.run()
