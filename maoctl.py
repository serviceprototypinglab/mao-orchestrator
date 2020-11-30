import arguments
import requests


def get_tools(*args):
    if len(args) == 0:
        r = requests.get('http://0.0.0.0:8080/registry/tools')
        print(r.json())
    else:
        r = requests.get('http://0.0.0.0:8080/registry/tools/' + args[0])
        print(r.json())


def get_datasets(*args):
    if len(args) == 0:
        r = requests.get('http://0.0.0.0:8080/registry/datasets')
        print(r.json())
    else:
        r = requests.get('http://0.0.0.0:8080/registry/datasets/' + args[0] + '/' + args[1])
        print(r.json())


def list_scheduled():
    r = requests.get('http://0.0.0.0:8080/jobs')
    print(r.json())


def list_local():
    r = requests.get('http://0.0.0.0:8080/files')
    print(r.json())


def add_dataset(name, node, url):
    #name = input("Name of dataset: ")
    #url = input("URL of dataset repo: ")
    json_out = {
    "name": name,
    "node": node,
    "url": url
    }
    r = requests.post('http://0.0.0.0:8080/registry/datasets', json=json_out)
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
    r = requests.post('http://0.0.0.0:8080/registry/tools', json=json_out)
    print(r.json())


def clone_dataset(name, node):
    r = requests.get('http://0.0.0.0:8080/files/clone/' + name + '/' + node)
    print(r.json())


def remove_tool(name):
    r = requests.delete('http://0.0.0.0:8080/registry/tools/' + name)
    print(r.json())


def remove_dataset(name, node):
    r = requests.delete('http://0.0.0.0:8080/registry/datasets/' + name + '/' + node)
    print(r.json())


def stop(id):
    r = requests.delete('http://0.0.0.0:8080/jobs/' + id)
    print(r.json())


def remove_local(name):
    r = requests.delete('http://0.0.0.0:8080/files/' + name)
    print(r.json())

def run_tool(name, *args):
    if len(args) == 2:
        json_out = {
        "name": name,
        "dataset": args[0],
        "node": args[1],
        "cron":False
        }
    else:
        json_out = {
        "name": name,
        "cron":False
        }
    r = requests.post('http://0.0.0.0:8080/jobs', json=json_out)
    response = r.json()
    print(response)


def renku_run(name, renku, *args):
    if len(args) == 2:
        json_out = {
        "name": name,
        "dataset": args[0],
        "node": args[1],
        "cron":False,
        "renku": renku
        }
    else:
        json_out = {
        "name": name,
        "cron":False,
        "renku": renku
        }
    r = requests.post('http://0.0.0.0:8080/jobs', json=json_out)
    response = r.json()
    print(response)


def schedule_tool(name, frequency, *args):
    #print(name, frequency)
    #for arg in args:
    #    print(arg)
    if len(args) == 2:
        json_out = {
        "name": name,
        "dataset": args[0],
        "node": args[1],
        "cron": True,
        "frequency": frequency
        }
    else:
        json_out = {
        "name": name,
        "cron":False,
        "frequency": frequency
        }
    r = requests.post('http://0.0.0.0:8080/jobs', json=json_out)
    response = r.json()
    print(response)


def schedule_renku(name, frequency, renku, *args):
    if len(args) == 2:
        json_out = {
        "name": name,
        "dataset": args[0],
        "node": args[1],
        "cron": True,
        "frequency": frequency,
        "renku": renku
        }
    else:
        json_out = {
        "name": name,
        "cron": True,
        "frequency": frequency,
        "renku": renku
        }
    r = requests.post('http://0.0.0.0:8080/jobs', json=json_out)
    response = r.json()
    print(response)



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
            if args.renku:
                if args.dataset and args.node:
                    renku_run(args.name, args.renku, args.dataset, args.node)
                else:
                    renku_run(args.name, args.renku)
            else:
                if args.dataset and args.node:
                    run_tool(args.name, args.dataset, args.node)
                else:
                    run_tool(args.name)
        elif args.tool == 'schedule':
            if args.renku:
                if args.dataset and args.node:
                    schedule_renku(args.name, args.frequency, args.renku, args.dataset, args.node)
                else:
                    schedule_renku(args.name, args.frequency, args.renku)
            else:
                if args.dataset and args.node:
                    schedule_tool(args.name,args.frequency, args.dataset, args.node)
                else:
                    schedule_tool(args.name, args.frequency)
        elif args.tool == 'remove':
            remove_tool(args.name)
        elif args.tool == 'list-scheduled':
            list_scheduled()
        elif args.tool == 'stop':
            stop(args.id)
    elif args.command == 'dataset':
        if args.dataset == 'get':
            if args.name and args.node:
                get_datasets(args.name, args.node)
            else:
                get_datasets()
        elif args.dataset == 'add':
            add_dataset(args.name, args.node, args.url)
        elif args.dataset == 'clone':
            clone_dataset(args.name, args.node)
        elif args.dataset == 'remove':
            remove_dataset(args.name, args.node)
        elif args.dataset == 'list-local':
            list_local()
        elif args.dataset == 'remove-local':
            remove_local(args.name)
