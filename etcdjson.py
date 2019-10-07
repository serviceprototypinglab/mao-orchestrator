import etcd
import json
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
importdir = config['WORKING_ENVIRONMENT']['IMPORTDIR']
etcd_host = config['ETCD']['HOST']
etcd_port = int(config['ETCD']['PORT'])
client = etcd.Client(host=etcd_host, port=etcd_port)

input = client.get('message').value
output = json.loads(input)
print(output['hello'])
