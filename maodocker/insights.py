import json
import etcd_client
import os


def report(path, tool, node):
    if os.path.isfile('{}/insights.json'.format(path)):
        with open('{}/insights.json'.format(path), 'r') as input:
            insights = json.load(input)
            print(insights)
            etcd_client.write('insight/{}/{}'.format(tool, node), json.dumps(insights))
