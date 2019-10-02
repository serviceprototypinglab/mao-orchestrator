from ruamel.yaml import YAML
import subprocess
from crontab import CronTab
import os
import syncer
import configparser

cron = CronTab(user=True)
output = {}
yaml = YAML()
yaml.preserve_quotes = True
config = configparser.ConfigParser()
config.read('config.ini')
importdir = config['WORKING_ENVIRONMENT']['IMPORTDIR']


def run_program(data):
    prog = syncer.get('tools/{}'.format(data['name']))
    command_string = "docker run -v {}/{}:/usr/src/app/data {}".format(importdir, data['name'], prog)
    subprocess.run(command_string, shell=True)
    diff_command = 'python3 differ.py {}/{} {}'.format(importdir, data['name'], data['dataset'])
    subprocess.run(diff_command, shell=True)
    """
    # Cron support disabled for replacement
    dir = os.getcwd()
    print(dir)
    if data['cron']:
        job = cron.new(command="cd {} && {} && {}".format(dir, command_string, diff_command))
        if data['frequency'] == 'daily':
            job.minute.on(0)
            job.hour.on(0)
        elif data['frequency'] == 'weekly':
            job.minute.on(0)
            job.hour.on(0)
            job.dow.on(0)
        elif data['frequency'] == 'monthly':
            job.minute.on(0)
            job.hour.on(0)
            job.dom.on(1)
        for item in cron:
            print(item)
        cron.write()
        for item in cron:
            print(item)
            """
    return
