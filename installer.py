import yaml
import secrets
import string
import os
import requests
import json

from typing import List
from pathlib import Path
from shutil import which
from marshmallow import Schema, fields, post_load
import marshmallow_objects as marshmallow
from requests.exceptions import HTTPError

class MaoClient:

    _URL = "http://127.0.0.1:8080"
    _URL_TOOLS = "registry/tools"

    class MaoTool(marshmallow.Model):
        name = fields.Str(required=True)
        image = fields.Str(required=True)
        author = fields.Str()
        data_repo = fields.URL()
        code_repo = fields.URL()
        artefact = fields.Str()
        # TODO maybe remove load_only from description in future
        description = fields.Str(load_only=False)
        federation_registered = fields.Bool(missing=False, load_only=True)
        instance_scheduled = fields.Bool(missing=False, load_only=True)

    @staticmethod
    def _remove_prefix(path):
        """Removed prefixed from absolute etcd paths"""
        _result = path.split('/')
        _last_index = len(_result)-1
        return _result[_last_index]

    def _api_get_tools(self):
        """Returns a list of tools registered with MAO"""
        r = requests.get(f"{self._URL}/{self._URL_TOOLS}")
        _tools = r.json()
        _result = []
        for tool in _tools:
            _result.append(MaoClient._remove_prefix(tool))
        return(_result)

    def _api_get_tool(self, name):
        """Returns detailed configuration of a single MAO tool"""
        r = requests.get(f"{self._URL}/{self._URL_TOOLS}/{name}")
        _tool = json.loads(r.json())
        return(_tool)

    def _api_add_tool(self, tool: dict):
        try:
            r = requests.post(f"{self._URL}/{self._URL_TOOLS}", json=tool)
            r.raise_for_status()
        except HTTPError as e:
            print(e)

    def get_tools(self):
        tools = []
        _tool_names = self._api_get_tools()
        for tool_name in _tool_names:
            _result = self._api_get_tool(tool_name)
            _result['name'] = tool_name
            tool = MaoClient.MaoTool.load(_result)
            tools.append(tool)
        
        return tools

    def add_tool(self, tool: MaoTool):
        serialized_tool = MaoClient.MaoTool.dump(tool)
        self._api_add_tool(serialized_tool)

class Installer:

    # MAO orchestrator dependencies
    dependencies = ['docker', 'docker-compose']

    def __init__(self):
        self.mao = MaoClient()

    def install(self):
        """Runs the interactive installer CLI"""

        # check if all dependencies are installed
        _dep_installed, _dep_name = self._check_dependencies()
        if _dep_installed == False:
            print(f"[Error] Missing MAO orchestrator dependency: {_dep_name}")
            exit(1)
        
        self.install_dir = input("Enter MAO install directory: ")
        self.instance_name = input("Enter MAO instance name (must match operator provided name): ")
        self.instance_ip = input("Enter the public IP of the new MAO instance: ")
        self.git_email = input("Enter your git config email address (used for MAO commits): ")
        self.ssh_key_dir = input("Enter directory containing ssh keys (used for git authentication): ")

        # let user choose if we join an existing federation or install a standalone/new federation
        _join_federation = Installer._ask_yes_no_question("Do you want to join an existing MAO federation?")
        if _join_federation:
            self.etcd_operator_input = input("Enter the operator provided etcd config: ")
            self.etcd_cluster_state = "existing"
        else:
            self.etcd_operator_input = f"{self.instance_name}=http://{self.instance_ip}:2380"
            self.etcd_cluster_state = "new"

        # auto generated parameters
        _alphabet = string.ascii_letters + string.digits
        self.scheduler_pw = ''.join(secrets.choice(_alphabet) for i in range(20))
        self.scheduler_db = "schedule"
        self.import_dir = "/home/user/data"
        self.etcd_client_port = "2379"
        self.etcd_subdir = "etcd"
        self.mao_subdir = "data"
        self.psql_subdir = "psql"

        # create MAO install directory
        # allow for shell-like shortcuts in path - returns absolute path
        self.install_dir = os.path.expanduser(self.install_dir)
        self._create_install_directories()

        # write generated docker-compose.yaml to install directory
        with open(f"{self.install_dir}/docker-compose.yaml", 'w') as file:
            yaml.dump(self._generate_compose(), file)

        print("\nMAO installer successfully finished!")
        print("\nUse the following commands to get your MAO instance up and running:")
        print(f"\t$ cd {self.install_dir}")
        print("\t$ docker-compose up")

    def initialize(self):
        # get MAO tools from different sources
        # get tools from current federation
        _tools_fed = self.mao.get_tools()
        for tool in _tools_fed:
            tool.federation_registered = True
        # get tools from marketplace
        _tools_market = self._get_marketplace()
        _tools = Installer._merge_tools(_tools_fed, _tools_market)

        # display tool selection on CLI
        print("Initialize instance...")
        print("\nAvailable MAO Tools:")
        # print tools
        Installer._print_tools(_tools)

        print("\nPlease select tools for activate on current instance (e.g. 1 2 4):")
        _input = input()
        try:
            _selected_tools = Installer._parse_tool_selection_input(_input)
            for selected in _selected_tools:
                self._add_tool_to_instance(_tools[selected])
        except TypeError as e:
            print(e)
            exit(1)

    @staticmethod
    def _merge_tools(base: List[MaoClient.MaoTool], additional: List[MaoClient.MaoTool]):
        # https://stackoverflow.com/a/58913412
        # generate base dict from input
        tools = {t.name: t for t in base}
        for tool in additional:
            if tool.name not in tools:
                tools[tool.name] = tool
        return list(tools.values())

    def _add_tool_to_instance(self, tool: MaoClient.MaoTool):
        """Adds MAO tool to current instance"""

        if not tool.federation_registered:
            # tool not existing in federation, add it
            self.mao.add_tool(tool)

        
        
    def _get_marketplace(self):
        """Read current selection of tools from MAO marketplace"""
        # TODO replace if query of actual marketplace, currently mocked via JSON file

        with open('marketplace.json') as marketplace_file:
            tools = json.load(marketplace_file)
            result = []
            for tool in tools:
                tool = MaoClient.MaoTool.load(tool)
                result.append(tool)
            return result

    @staticmethod
    def _parse_tool_selection_input(input):
        _input = input.split(" ")
        _result = []
        for number in _input:
            # check if numeric
            if number.isnumeric():
                _result.append(int(number))
            else:
                raise TypeError(f"Invalid input, {number} is not a number!")
        return _result

    @staticmethod
    def _print_tools(tools):
        for i, tool in enumerate(tools):
            print(f"[{i}] {tool.name}, " \
                f"federation {Installer._print_boolean_symbol(tool.federation_registered)}, " \
                f"instance {Installer._print_boolean_symbol(tool.instance_scheduled)}")

    @staticmethod
    def _print_boolean_symbol(bool: bool):
        return '✓' if bool else '✗'

    @staticmethod
    def _ask_yes_no_question(prompt):
        
        _answer = input(f"{prompt} - [y/n]: ")
        if _answer == "y":
            return True
        elif _answer == "n":
            return False
        else:
            print(f"'{_answer}' does not match the expected input of 'y' for yes and 'n' for no. Please try again...")
            return Installer._ask_yes_no_question(prompt)

    def _create_install_directories(self):
        """Create directory structure and permissions for installation"""

        # UID of the process inside the mao container
        _mao_uid = 1000

        try:
            Path(self.install_dir).mkdir(parents=True, exist_ok=True)
            Path(f"{self.install_dir}/{self.etcd_subdir}").mkdir(parents=True, exist_ok=True)
            Path(f"{self.install_dir}/{self.psql_subdir}").mkdir(parents=True, exist_ok=True)
            Path(f"{self.install_dir}/{self.mao_subdir}").mkdir(parents=True, exist_ok=True)
            os.chown(f"{self.install_dir}/{self.mao_subdir}", _mao_uid, -1)
        except PermissionError:
            print(f"[Error] Permission to create directory '{self.install_dir}' denied.")
            exit(1)

    def _check_dependencies(self):
        """Checks if all dependencies of MAO are present on the system"""

        for dep in self.dependencies:
            if which(dep) is None:
                return False, dep

        return True, None

    def _generate_compose(self):
        """Generate the Docker Compose YAML based on the user inputs"""

        # Python object representation of docker-compose.yaml
        compose = {
            "version": "3",
            "services": {
                # MAO orchestrator
                "mao": {
                    # TODO switch to docker registry provided MAO image
                    "image": "local/mao",
                    "environment": [
                        f"importdir={self.import_dir}",
                        f"hostdir={self.install_dir}/{self.mao_subdir}",
                        f"workuser={self.instance_name}",
                        f"etcdhost={self.instance_ip}",
                        f"port={self.etcd_client_port}",
                        f"dbuser={self.scheduler_db}",
                        f"password={self.scheduler_pw}",
                        f"db={self.scheduler_db}",
                        "dbhost=127.0.0.1",
                        f"gitemail={self.git_email}",
                        f"gitusername={self.instance_name}"
                    ],
                    "volumes": [
                        # mount data directory from host
                        f"{self.install_dir}/{self.mao_subdir}:{self.import_dir}",
                        # mount git used ssh keys directory
                        f"{self.ssh_key_dir}:/home/user/.ssh"
                    ],
                    "network_mode": "host",
                    "depends_on": [
                        "etcd",
                        "db"
                    ]
                },
                # MAO tool executor
                "executor": {
                    # TODO switch to docker registry provided MAO image
                    "image": "local/executor",
                    "volumes": [
                        # mount Docker socket for container execution
                        "/var/run/docker.sock:/var/run/docker.sock"
                    ],
                    "network_mode": "host",
                    "depends_on": [
                        "mao"
                    ]
                },
                # MAO scheduler job store
                "db": {
                    "image": "postgres:13.2",
                    "environment": [
                        f"POSTGRES_DB={self.scheduler_db}",
                        f"POSTGRES_PASSWORD={self.scheduler_pw}",
                        f"POSTGRES_USER={self.scheduler_db}"
                    ],
                    "volumes": [
                        # mount postgresql data directory
                        f"{self.install_dir}/{self.psql_subdir}:/var/lib/postgresql/data"
                    ],
                    "network_mode": "host"
                },
                # MAO etcd distributed k/v store
                "etcd": {
                    "image": "quay.io/coreos/etcd:v3.4.15",
                    "environment": [
                        "ALLOW_NONE_AUTHENTICATION=yes",
                        "ETCD_ENABLE_V2=true",
                        f"ETCD_NAME={self.instance_name}",
                        "ETCD_DATA_DIR=/etcd-data",
                        f"ETCD_INITIAL_ADVERTISE_PEER_URLS=http://{self.instance_ip}:2380",
                        f"ETCD_LISTEN_PEER_URLS=http://{self.instance_ip}:2380",
                        f"ETCD_LISTEN_CLIENT_URLS=http://{self.instance_ip}:{self.etcd_client_port}",
                        f"ETCD_ADVERTISE_CLIENT_URLS=http://{self.instance_ip}:{self.etcd_client_port}",
                        #"ETCD_INITIAL_CLUSTER_TOKEN=etcd-cluster",
                        f"ETCD_INITIAL_CLUSTER_STATE={self.etcd_cluster_state}",
                        f"ETCD_INITIAL_CLUSTER={self.etcd_operator_input}"
                    ],
                    "volumes": [
                        # mount etcd data directory
                        f"{self.install_dir}/{self.etcd_subdir}:/etcd-data"
                    ],
                    "network_mode": "host"
                }
            }
        }

        return compose