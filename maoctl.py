import arguments
import requests


def get_tools(*args):
    if len(args) == 0:
        r = requests.get('http://0.0.0.0:8080/regtools')
        print(r.json())
    else:
        r = requests.get('http://0.0.0.0:8080/regtools/' + args[0])
        print(r.json())


def get_datasets(*args):
    if len(args) == 0:
        r = requests.get('http://0.0.0.0:8080/datasets')
        print(r.json())
    else:
        r = requests.get('http://0.0.0.0:8080/datasets/' + args[0])
        print(r.json())


def list_scheduled():
    r = requests.get('http://0.0.0.0:8080/jobslist')
    print(r.json())


def list_local():
    r = requests.get('http://0.0.0.0:8080/locallist')
    print(r.json())


def add_dataset(name, url):
    #name = input("Name of dataset: ")
    #url = input("URL of dataset repo: ")
    json_out = {
    "name": name,
    "url": url
    }
    r = requests.post('http://0.0.0.0:8080/regdata', json=json_out)
    print(r.json())


def add_tool(name, author, image, data_repo, code_repo, artefact):
    json_out = {
    "name": name,
    "author": author,
    "image": image,
    "data_repo": data_repo,
    "code_repo": code_repo,
    "artefact": artefact
    }
    r = requests.post('http://0.0.0.0:8080/register', json=json_out)
    print(r.json())


def clone_dataset(name):
    json_out = {
    "name": name
    }
    r = requests.post('http://0.0.0.0:8080/retrieve', json=json_out)
    print(r.json())


def remove_tool(name):
    json_out = {
    "name": name
    }
    r = requests.post('http://0.0.0.0:8080/tooldelete', json=json_out)
    print(r.json())


def remove_dataset(name):
    json_out = {
    "name": name
    }
    r = requests.post('http://0.0.0.0:8080/datadelete', json=json_out)
    print(r.json())


def stop(id):
    json_out = {
    "id": id
    }
    r = requests.post('http://0.0.0.0:8080/jobdelete', json=json_out)
    print(r.json())


def remove_local(name):
    json_out = {
    "name": name
    }
    r = requests.post('http://0.0.0.0:8080/localdelete', json=json_out)
    print(r.json())


def audit(name):
    json_out = {
    "name": name
    }
    r = requests.post('http://0.0.0.0:8080/audit', json=json_out)
    print(r.json())


def run_tool(name):
    json_out = {
    "name": name,
    "cron":False
    }
    r = requests.post('http://0.0.0.0:8080/run', json=json_out)
    response = r.json()
    print("Report:")
    print("Tool image: " + response['tool'])
    print("Data directory: " + response['datadir'])
    print("Message to scheduler: " + response['message'])
    print("Scheduler output: ")
    print("Tool image: " + response['scheduler_output']['container'])
    print("Name of tool: " + response['scheduler_output']['tool'])
    print("Data directory: " + response['scheduler_output']['dataset'])
    print("Spike detector output:")
    print("Data directory: " + response['scheduler_output']['exec_result']['datapath'])
    print("Number of data snapshots: " + str(response['scheduler_output']['exec_result']['snapshots']))
    print("Current rolling average of control metric: " + str(response['scheduler_output']['exec_result']['rolling_avg']))
    print("Value of control metric in current snapshot: " + str(response['scheduler_output']['exec_result']['control_metric']))
    print("Difference:" + str(response['scheduler_output']['exec_result']['diff']))
    print("Gain:" + str(round(response['scheduler_output']['exec_result']['gain'],2)) + "%")
    if response['scheduler_output']['exec_result']['spike']:
        print("Spike detected. Notification writen to cluster")
    else:
        print("No data anomalies detected")



def schedule_tool(name, frequency):
    json_out = {
    "name": name,
    "cron": True,
    "frequency": frequency
    }
    r = requests.post('http://0.0.0.0:8080/run', json=json_out)
    response = r.json()
    print("Report:")
    print("Tool image: " + response['tool'])
    print("Data directory: " + response['datadir'])
    print("Message to scheduler: " + response['message'])
    print("Scheduler output: ")
    print("Tool image: " + response['scheduler_output']['container'])
    print("Name of tool: " + response['scheduler_output']['tool'])
    print("Data directory: " + response['scheduler_output']['dataset'])
    print("ID of scheduled job: " + response['scheduler_output']['job'])



if __name__ == '__main__':
    arguments = arguments.Arguments()
    args = arguments.args
    if args.command == 'tool':
        if args.tool == 'get':
            if args.name:
                get_tools(args.name)
            else:
                get_tools()
        elif args.tool == 'add':
            add_tool(args.name, args.author, args.image, args.data_repo,
                     args.code_repo,args.artefact)
        elif args.tool == 'run':
            run_tool(args.name)
        elif args.tool == 'schedule':
            schedule_tool(args.name, args.frequency)
        elif args.tool == 'remove':
            remove_tool(args.name)
        elif args.tool == 'list-scheduled':
            list_scheduled()
        elif args.tool == 'stop':
            stop(args.id)
    elif args.command == 'dataset':
        if args.dataset == 'get':
            if args.name:
                get_datasets(args.name)
            else:
                get_datasets()
        elif args.dataset == 'add':
            add_dataset(args.name, args.url)
        elif args.dataset == 'clone':
            clone_dataset(args.name)
        elif args.dataset == 'remove':
            remove_dataset(args.name)
        elif args.dataset == 'list-local':
            list_local()
        elif args.dataset == 'remove-local':
            remove_local(args.name)
        elif args.dataset == 'audit':
            audit(args.name)
