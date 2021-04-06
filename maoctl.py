import arguments
import requests
from installer import Installer


def get_tools(*args):
    if len(args) == 0:
        r = requests.get('http://0.0.0.0:8080/registry/tools')
        print(r.json())
    else:
        r = requests.get('http://0.0.0.0:8080/registry/tools/' + args[0])
        print(r.json())

def list_scheduled():
    r = requests.get('http://0.0.0.0:8080/jobs')
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

def remove_tool(name):
    r = requests.delete('http://0.0.0.0:8080/registry/tools/' + name)
    print(r.json())


def stop(id):
    r = requests.delete('http://0.0.0.0:8080/jobs/' + id)
    print(r.json())


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
        elif args.tool == 'remove':
            remove_tool(args.name)
        elif args.tool == 'list-scheduled':
            list_scheduled()
        elif args.tool == 'stop':
            stop(args.id)
    elif args.command == 'install':
        Installer().run()