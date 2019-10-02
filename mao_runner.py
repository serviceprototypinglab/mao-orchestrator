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
    return
