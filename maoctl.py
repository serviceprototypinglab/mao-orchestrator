from typing import List, Optional

import requests

from arguments import Arguments
from installer import Installer

_URL = "http://0.0.0.0:8080"
_URL_TOOLS = "registry/tools"
_URL_DATASETS = "registry/datasets"
_URL_PIPELINE_REG = "registry/pipelines"
_URL_PIPELINE = "pipeline"


def get_tools(name: Optional[str] = None):
    if not name or name.strip() == "":
        r = requests.get(f"{_URL}/{_URL_TOOLS}")
        print(r.json())
    else:
        r = requests.get(f"{_URL}/{_URL_TOOLS}/{name}")
        print(r.json())


def get_datasets(name: Optional[str] = None):
    if not name or name.strip() == "":
        r = requests.get(f"{_URL}/{_URL_DATASETS}")
        print(r.json())
    else:
        r = requests.get(f"{_URL}/{_URL_DATASETS}/{name}")
        print(r.json())


def get_pipelines(name: Optional[str] = None):
    if not name or name.strip() == "":
        r = requests.get(f"{_URL}/{_URL_PIPELINE}")
        _pipelines = [p["name"] for p in r.json()]
        print(_pipelines)
    else:
        r = requests.get(f"{_URL}/{_URL_PIPELINE_REG}/{name}")
        print(r.json())


def get_jobs():
    r = requests.get(f"{_URL}/jobs")
    print(r.json())


def add_tool(name, author, image, data_repo, code_repo, artefact):
    json_out = {
        "name": name,
        "author": author,
        "image": image,
        "data_repo": data_repo,
        "code_repo": code_repo,
        "artefact": artefact,
    }
    r = requests.post(f"{_URL}/{_URL_TOOLS}", json=json_out)
    print(r.json())


def add_dataset(name, url):
    json_out = {
        "name": name,
        "body": {
            "master": url,
            "nodes": [],
        },
    }
    r = requests.post(f"{_URL}/{_URL_DATASETS}", json=json_out)
    print(r.json())


def add_repo(name: Optional[str] = None):
    if not name or name.strip() == "":
        print("Please provide a tool name")
        return None

    req = dict()
    req["name"] = name

    r = requests.post(f"{_URL}/bare-repo/init", json=req)
    if r.ok:
        print("Successfully initialized a local repo")
    else:
        print("Repo initialization failed")
    print(r.json())


def remove_tool(name: Optional[str] = None):
    if not name or name.strip() == "":
        print("Please provide a tool name")
        return None

    r = requests.delete(f"{_URL}/{_URL_TOOLS}/{name}")
    print(r.json())


def remove_dataset(name: Optional[str] = None):
    if not name or name.strip() == "":
        print("Please provide a dataset name")
        return None

    r: requests.Response = requests.delete(f"{_URL}/{_URL_DATASETS}/{name}")
    if r.ok:
        print(f"Dataset '{name}' successfully deleted.")
    else:
        print(f"There was an error deleting '{name}'.")


def stop(id):
    r = requests.delete(f"{_URL}/jobs/{id}")
    print(r.json())


def __build_pipeline_step() -> dict:
    step = dict()
    step["name"] = promt_for_valid_identifier("Pleasre provide the pipeline step name. ex: step_1\nStep name: ")
    step["tool"] = promt_for_non_empty_str(
        "Please enter the tool identifier that is used in the step.\nTool identifier: "
    )
    step["input_dataset"] = input("Please enter the tool input_dataset.\nTool input_dataset: ")
    if step["input_dataset"].strip() == "":
        step["input_dataset"] = None
    step["output_dataset"] = promt_for_non_empty_str("Please enter the tool output_dataset.\nTool output_dataset: ")
    step["docker_socket"] = yes_no_promt("Does the tool require a docker socket?")
    # TODO: update these with relevant data.
    step["cmd"] = {}
    step["env"] = {}
    return step


def yes_no_promt(message: str) -> bool:
    while True:
        q = input(f"{message} [y/n]: ")
        if q == "y":
            return True
        elif q == "n":
            return False
        else:
            print("\nPlease choose between y - Yes and n - No\n")


def promt_for_valid_identifier(message: str) -> str:
    name_valid: bool = False
    name_promt: Optional[str] = f"{message}"
    while not name_valid:
        name: str = input(name_promt)
        name = name.strip()
        name_valid = name.isidentifier()
        if not name_valid:
            print(f"\nName '{name}' cannot be used as an identifier. Please enter a valid name\n")
            name_promt = message.split("\n")[-1]

    return name


def promt_for_non_empty_str(message: str) -> str:
    str_valid: bool = False
    while not str_valid:
        value: str = input(message)
        value = value.strip()
        str_valid = value != ""
        if not str_valid:
            print(f"\nPlease enter a non-empty value\n")
    return value


def add_pipeline():
    pipeline = dict()
    pipeline["name"] = promt_for_valid_identifier(
        "Please provide a pipeline name. ex: my_awesome_pipeline\nPipeline name: "
    )
    pipeline["description"] = input(
        "Please provide pipeline description ex. Pipeline to evaluate system performance\nPipeline description: "
    )

    steps: List[dict] = []
    print("\nPlease create the pipeline steps\n")
    while len(steps) == 0 or yes_no_promt("Add another step?"):
        step: dict = __build_pipeline_step()
        steps.append(step)

    pipeline["steps"] = steps
    r: requests.Response = requests.post(f"{_URL}/pipeline/init", json=pipeline)
    if r.ok:
        print("Pipeline created successfully")
        print(r.json())
    else:
        resp = r.json()
        print("Pipeline creation failed")
        print(resp["errors"])


def run_pipeline(name: Optional[str] = None):
    if not name or name.strip() == "":
        print("Please provide a tool name")
        return None
    req = dict()
    req["name"] = name
    req["cron"] = None  # TODO(fix)
    r: requests.Response = requests.post(f"{_URL}/pipeline/run", json=req)
    if not r.ok:
        print("There was an error running the pipeline")
    print(r.json())


if __name__ == "__main__":
    arguments = Arguments()
    args = arguments.parse_args()

    if args.command == "tool":
        if args.tool == "get":
            if args.name:
                get_tools(args.name)
            else:
                get_tools()
        elif args.tool == "add":
            add_tool(args.name, args.author, args.image, args.data_repo, args.code_repo, args.artefact)
        elif args.tool == "remove":
            remove_tool(args.name)
        elif args.tool == "list-scheduled":
            get_jobs()
        elif args.tool == "stop":
            stop(args.id)
    elif args.command == "instance":
        if args.instance == "install":
            Installer().install()
        elif args.instance == "init":
            Installer().initialize()
    elif args.command == "dataset":
        if args.dataset == "get":
            if args.name:
                get_datasets(args.name)
            else:
                get_datasets()
        elif args.dataset == "add":
            add_dataset(args.name, args.git_url)
        elif args.dataset == "remove":
            remove_dataset(args.name)
    elif args.command == "pipeline":
        if args.pipeline == "get":
            if args.name:
                get_pipelines(args.name)
            else:
                get_pipelines()
        elif args.pipeline == "add":
            add_pipeline()
        elif args.pipeline == "run":
            run_pipeline(args.name)
    elif args.command == "repo":
        if args.repo == "add":
            add_repo(args.name)
