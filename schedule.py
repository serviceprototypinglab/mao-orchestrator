from apscheduler.schedulers.background import BackgroundScheduler
import differ
import docker
import configparser
import etcd


docker_client = docker.from_env()
config = configparser.ConfigParser()
config.read('config.ini')
importdir = config['WORKING_ENVIRONMENT']['IMPORTDIR']
etcd_host = config['ETCD']['HOST']
etcd_port = int(config['ETCD']['PORT'])
client = etcd.Client(host=etcd_host, port=etcd_port)
scheduler = BackgroundScheduler()
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
                                    args=[container, tool, dataset],
                                    misfire_grace_time=None, coalesce=True)
        elif freq == 'weekly':
            job = scheduler.add_job(run_container, 'interval', weeks=1,
                                    args=[container, tool, dataset],
                                    misfire_grace_time=None, coalesce=True)
        response['job'] = job.id
        return response
    else:
        response['exec_result'] = run_container(container, tool, dataset)
        return response


def run_container(container, tool, dataset):
    result = {}
    docker_client.containers.run(container,
                                 volumes={dataset: {'bind': '/usr/src/app/data'}})
    result = differ.detect(dataset, tool)
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


scheduler.add_job(listen, 'interval', seconds=10,
                  misfire_grace_time=None, coalesce=True)