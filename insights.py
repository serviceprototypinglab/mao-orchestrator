import json
import syncer


def report(path, tool, node):
    with open('{}/insights.json'.format(path), 'r') as input:
        insights = json.load(input)
        print(insights)
        syncer.write('insight/{}/{}'.format(tool, node), json.dumps(insights))
