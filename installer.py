import yaml
import secrets
import string
import os
import requests
import json
import numpy as np
import subprocess
import socket
import ipaddress
import getpass

from apscheduler.triggers.cron import CronTrigger
from typing import List
from pathlib import Path
from shutil import ExecError, which
from marshmallow import fields, EXCLUDE
import marshmallow_objects as marshmallow
from requests.exceptions import HTTPError

import api_client as MaoClient
import marketplace as MaoMarketplace

class Installer:

    # MAO orchestrator dependencies
    dependencies = ['docker', 'docker-compose']
    MAO_DEFAULT_INSTALL_DIR = f"{Path.home()}/mao-instance"
    MAO_CLI_SPACEING = "   "

    def install(self):
        """Runs the interactive installer CLI"""

        # check if all dependencies are installed
        _dep_installed, _dep_name = self._check_dependencies()
        if _dep_installed == False:
            print(f"[Error] Missing MAO orchestrator dependency: {_dep_name}")
            exit(1)

        # handle input validation exceptions
        try:
            ### MAO federation join
            # let user choose if we join an existing federation or install a standalone/new federation
            _join_federation = Installer._ask_yes_no_question("Do you want to join an existing MAO federation?")
            if _join_federation:
                print("") # insert blank line
                # check if federation operator has already been contacted
                _options = [
                    "List available federations from MAO marketplace",  # 0
                    "Proceed with federation join"                      # 1
                ]
                Installer._print_options(_options)
                _input = input("\nPlease choose an option: ")
                _selected_option = Installer._parse_numeric_single(_input, _options)
                
                if _selected_option == 0:
                    # list federations from marketplace
                    self.marketplace_fed_cli()
                elif _selected_option == 1:
                    # ask user for etcd details
                    self.etcd_operator_input = input("\nEnter the operator provided etcd config: ")
                    self.etcd_cluster_state = "existing"
            print("") # insert blank line
            
            ### MAO install directory
            self.install_dir = input(f"Enter MAO install directory (or leave empty for '{self.MAO_DEFAULT_INSTALL_DIR}'): ")
            if self.install_dir == "":
                # empty user input, use default
                self.install_dir = Installer.MAO_DEFAULT_INSTALL_DIR
            print("") # insert blank line

            ### MAO instance name
            self.instance_name = input(f"Enter MAO instance name (if you join a federation, this must match operator provided name; for local-only use cases leave empty to use '{socket.gethostname()}'): ")
            if self.instance_name == "":
                # empty user input, use hostname
                self.instance_name = socket.gethostname()
            print("") # insert blank line

            ### MAO IP address config
            print("MAO needs some IP configuration in order to work well in different scenarios.\n"
                +"Please make sure that your instance can be reached from others via the selected IP on port 2380, select the appropriate option:")
            _ip_selection = [
                Installer._get_public_ip(),
                Installer._get_host_ip(),
                "manual"
            ]
            print(f"{self.MAO_CLI_SPACEING}[0] Public IP - in federated setups it might be necessary to use the instances non-local public IP so that other instances can reach your instance, the following IP was auto-detected: {str(_ip_selection[0])}")
            print(f"{self.MAO_CLI_SPACEING}[1] Host IP - if other instances can reach your instance via an interface IP or in local-only setups you can use the hosts IP, the following IP was auto-detected: {str(_ip_selection[1])}")
            print(f"{self.MAO_CLI_SPACEING}[2] Manual - manually enter the IP to use for your instance")
            self.instance_ip = input("Enter your selection for the desired IP setup (e.g. 1): ")
            self.instance_ip = Installer._parse_numeric_single(self.instance_ip, _ip_selection)
            self.instance_ip = _ip_selection[self.instance_ip]
            if self.instance_ip == "manual":
                self.instance_ip = input("Please enter the IP address to use for your instance configuration: ")
            Installer._validate_ip(self.instance_ip)
            print("") # insert blank line

            ### MAO commit e-mail config
            _default_mail_dummy = f"{getpass.getuser()}@{self.instance_name}"
            self.git_email = input(f"Enter your git config email address (used for MAO commits; leave empty to use default dummy: {_default_mail_dummy}): ")
            if self.git_email == "":
                self.git_email = _default_mail_dummy
            print("") # insert blank line

            ### MAO SSH path setup
            self.ssh_key_dir = input("Enter directory containing ssh keys (used for git authentication; leave empty for local-only use cases): ")
            if self.ssh_key_dir == "":
                self.ssh_key_dir = None

            if not _join_federation:
                self.etcd_operator_input = f"{self.instance_name}=http://{self.instance_ip}:2380"
                self.etcd_cluster_state = "new"

        except (TypeError, IndexError, ValueError) as e:
                print(e)
                exit(1)

        # auto generated parameters
        _alphabet = string.ascii_letters + string.digits
        self.scheduler_pw = ''.join(secrets.choice(_alphabet) for i in range(20))
        self.scheduler_db = "schedule"
        self.import_dir = "/home/user/data"
        self.etcd_client_port = "2379"
        self.etcd_subdir = "etcd"
        self.mao_subdir = "data"
        self.psql_subdir = "psql"
        self.bare_subdir = "bare"

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

        try:
            # import pipelines
            # get pipelines from marketplace
            _pipelines_market = MaoMarketplace.Pipeline.list()
            # get pipelines from local instance
            _pipelines_local = MaoClient.Pipeline.list()
            for pipe in _pipelines_local:
                pipe.instance_scheduled = True
            _pipelines = np.array(Installer._merge_tools(_pipelines_local, _pipelines_market))

            print("\nAvailable MAO Pipelines ('✓'/'✗' indicate if pipline is already registered with this instance or federation):\n")
            Installer._print_pipelines(_pipelines)

            print("\nPlease select pipelines for activation on this instance (e.g. 1 2 4):")
            _input = input()
            print("") # insert blank line
            try:
                _selected_pipelines = Installer._parse_numeric_multi(_input, _pipelines)
                for selected_pipeline in list(_pipelines[_selected_pipelines]):
                    if selected_pipeline.instance_scheduled:
                        print(f"{selected_pipeline.name} already present on your instance, readding currently not supported, skipping ...\n")
                        continue

                    _private_vars = selected_pipeline.get_private_vars()
                    # check if private vars exist
                    if _private_vars:
                        for step, env in _private_vars.items():
                            for var in env.keys():
                                print(f"Please enter a value for the private variable {var}:")
                                _input = input()
                                print("") # insert blank line

                                _private_vars[step][var] = _input

                    selected_pipeline.set_private_vars(_private_vars)

                    api_result = selected_pipeline.init()
                    # check if api returned an error
                    if not api_result.get('ok', False):
                        # check if api returned missing datasets
                        if len(api_result.get('errors').get('missing_datasets')) >= 1:
                            print(f"[Error] Skipped pipeline initialization for {selected_pipeline.name}, " \
                                f"as the following datasets were discovered to be missing: {api_result['errors']['missing_datasets']}.\n")
                            
                            _ask_local_only = Installer._ask_yes_no_question(
                                f"You have the possibility to add the missing datasets as local-only to the federation.\n" \
                                "This is especially useful for demoing and explorational use cases in single node federations.\n" \
                                "Acquired data will only be saved locally on this instance and not shared with other instances in the federation.\n" \
                                "Do you want to add the missing datasets as local-only?"
                                )

                            if _ask_local_only:
                                # create and init local-only git structure
                                for dataset in api_result['errors']['missing_datasets']:
                                    _bare = MaoClient.BareRepo.load({"name": dataset})
                                    _bare.init()
                                    _dataset = MaoClient.Dataset.load({
                                        "name": _bare.name,
                                        "master": _bare.path,
                                        "nodes": []
                                    })
                                    _dataset.add()

                                # try to add pipeline again after registering missing datasets
                                api_result = selected_pipeline.init()
                            else:
                                continue

                        # check if api returned missing tools
                        if not api_result.get('ok', False):
                            if len(api_result.get('errors').get('missing_tools')) >= 1:
                                _missing_tools = api_result['errors']['missing_tools']
                                _add_missing_tools = Installer._ask_yes_no_question(
                                    f"The following missing tools have been detected: {_missing_tools}\n" \
                                    "Do you want the installer to add them from the marketplace?"
                                    )
                                if _add_missing_tools:
                                    self._add_tools(_missing_tools)
                                else:
                                    print(f"Skipped pipeline {selected_pipeline.name}, continue with next one ...\n")
                                    continue
                                api_result = selected_pipeline.init()
                                print("") # insert blank line
                                if not api_result.get('ok', False):
                                    raise Exception("Pipeline initialization failed irrecoverably.")

                    _ask_schedule = Installer._ask_yes_no_question(f"Do you want to schedule {selected_pipeline.name} now?", new_line=True)
                    if _ask_schedule:
                        # run/schedule pipeline
                        # ask user to enter cron schedule for tool
                        print(f"Please enter crontab to schedule {selected_pipeline.name} (e.g. '0 12 * * *'):")
                        print(f"  > Hint: if you are not sure what to enter here, please contact your federation " \
                                "operator to get more information about pipeline schedules.")
                        _input = input()
                        print("") # insert blank line
                        _cron = Installer._parse_cron(_input)

                        selected_pipeline.run(_cron)

                    print(f"Successfully added pipeline {selected_pipeline.name}, continue with next one ...\n")

            except (TypeError, IndexError, ValueError) as e:
                print(e)
                exit(1)

            print("Instance successfully initialized, re-run the initialization command to register additional pipelines.")
                
        except requests.exceptions.RequestException as e:
            print(f"\n [Error] The following error occurred while trying to reach the orchestrator: \n {e}")
            print("\n Are you sure the MAO orchestrator is up and running?")
            exit(1)

    @staticmethod
    def _get_public_ip():
        """Uses public web-service to discover public IP of requesting host"""
        ip = requests.get("https://checkip.dedyn.io/")
        if ip.ok:
            return ip.content.decode("utf-8") 
        else:
            return None

    @staticmethod
    def _get_host_ip():
        """Returns the interface IP of the local instance"""
        # Ref: https://stackoverflow.com/a/25850698/3416025
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 1))  # connect() for UDP doesn't send packets, so the IP here is arbitrary
        return s.getsockname()[0]

    @staticmethod
    def _validate_ip(ip):
        """Checks if the input string contains a valid IP address"""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError as e:
            print(f"[Error] The given IP address is invalid or malformed: {ip}")
            raise e

    @staticmethod
    def _merge_tools(base: List[MaoClient.Tool], additional: List[MaoClient.Tool]):
        """Merges to lists of MAO tools with precedence on base"""
        
        # https://stackoverflow.com/a/58913412
        # generate base dict from input
        tools = {t.name: t for t in base}
        for tool in additional:
            if tool.name not in tools:
                tools[tool.name] = tool
        return list(tools.values())

    def marketplace_fed_cli(self):
        federations = MaoMarketplace.Federation.list()
        print("") # insert blank line
        print("Available federations on the MAO marketplace:")
        Installer._print_federation(federations)
        _input = input("\nPlease select a federation to join (e.g. 1): ")
        print("") # insert blank line
        _selected_fed = Installer._parse_numeric_single(_input, federations)
        print("Please get in contact with one of the federation operators in order to join:")
        Installer._print_federation_contacts(federations[_selected_fed])

        print("\nPlease provide the operators with the following information:\n" \
            "- Instance IP-Address\n" \
            "- Desired instance name\n" \
            "- SSH public key of this instance for authentication to the dataset repositories")

        print("\nJust launch the installer again after the federation operator provided the necessary information.")
        exit(0)

    @staticmethod
    def _parse_numeric_multi(input, selection_base: list):
        _input = input.split(" ")
        _result = []
        for number in _input:
            # check if numeric
            if number.isnumeric():
                _result.append(int(number))
            else:
                raise TypeError(f"Invalid input, {number} is not a number!")
            # check if index is in bounds
            if int(number) < 0 or int(number) >= len(selection_base):
                _available_indexes = list(range(0, len(selection_base)-1))
                raise IndexError(f"Input '{number}' is not one of {_available_indexes}")
        return _result

    @staticmethod
    def _parse_numeric_single(input, selection_base: list):
        # check if input is numberic
        if not input.isnumeric():
            raise TypeError(f"Invalid input, {input} is not a number!")
        # check if index is in bounds
        if int(input) < 0 or int(input) >= len(selection_base):
            _available_indexes = list(range(0, len(selection_base)))
            raise IndexError(f"Input '{input}' is not one of {_available_indexes}")
        return int(input)

    @staticmethod
    def _parse_cron(input):
        try:
            # use apscheduler CronTrigger for crontab syntax validation
            CronTrigger.from_crontab(input)
            return input
        except ValueError as e:
            raise ValueError(f"Input is not a valid crontab - {e}")

    @staticmethod
    def _print_tools(tools):
        for i, tool in enumerate(tools):
            print(f"[{i}] {tool.name}, " \
                f"federation {Installer._print_boolean_symbol(tool.federation_registered)}, " \
                f"instance {Installer._print_boolean_symbol(tool.instance_scheduled)}")

    @staticmethod
    def _print_pipelines(pipelines):
        for i, pipeline in enumerate(pipelines):
            print(f"[{i}] {pipeline.name} | registered on: " \
                f"this instance {Installer._print_boolean_symbol(pipeline.instance_scheduled)},",
                f"this federation {Installer._print_boolean_symbol(pipeline.federation_registered)}"
                )
            if hasattr(pipeline, 'description'):
                print(f"\tDescription: '{pipeline.description}'")
    
    @staticmethod
    def _print_datasets(datasets: List[MaoClient.Dataset]):
        for i, dataset in enumerate(datasets):
            print(f"[{i}] {dataset.name}, " \
                f"{dataset.master}, " \
                f"nodes: {dataset.nodes}")

    @staticmethod
    def _print_federation(federations: List[MaoMarketplace.Federation]):
        for i, fed in enumerate(federations):
            print(f"[{i}] {fed.name} - " \
                f"{fed.description}")

    @staticmethod
    def _print_federation_contacts(federation: MaoMarketplace.Federation):
        for contact in federation.contacts:
            print(f"- {contact}")

    @staticmethod
    def _print_options(options: List[str]):
        for i, option in enumerate(options):
            print(f"[{i}] {option}")

    @staticmethod
    def _print_boolean_symbol(bool: bool):
        return '✓' if bool else '✗'

    @staticmethod
    def _ask_yes_no_question(prompt, new_line=False):
        
        _answer = input(f"{prompt} - [y/n]: ")
        if new_line:
            print("")
        if _answer == "y":
            return True
        elif _answer == "n":
            return False
        else:
            print(f"'{_answer}' does not match the expected input of 'y' for yes and 'n' for no. Please try again...")
            return Installer._ask_yes_no_question(prompt)

    def _add_tools(self, tool_names: List):
        """Tries to add a list of tools to the current instance based on their names"""
        _tools_market = MaoMarketplace.Tool.list()

        for tool in _tools_market:
            if tool.name in tool_names:
                print(f"> Adding new tool {tool.name} to federation.")
                tool.add()
                tool_names.remove(tool.name)

        if len(tool_names) != 0:
            # some tools have not been found on the marketplace
            raise Exception(f"The following tools have not been found on the marketplace: {tool_names}")
            

    def _create_install_directories(self):
        """Create directory structure and permissions for installation"""

        # UID of the process inside the mao container
        _mao_uid = 1000

        try:
            Path(self.install_dir).mkdir(parents=True, exist_ok=True)
            Path(f"{self.install_dir}/{self.etcd_subdir}").mkdir(parents=True, exist_ok=True)
            Path(f"{self.install_dir}/{self.psql_subdir}").mkdir(parents=True, exist_ok=True)
            Path(f"{self.install_dir}/{self.mao_subdir}").mkdir(parents=True, exist_ok=True)
            Path(f"{self.install_dir}/{self.bare_subdir}").mkdir(parents=True, exist_ok=True)
            os.chown(f"{self.install_dir}/{self.mao_subdir}", _mao_uid, -1)
            os.chown(f"{self.install_dir}/{self.bare_subdir}", _mao_uid, -1)
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
                        f"etcdhost=127.0.0.1",
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
                        # handling of ssh key directory below the dict definition due to conditional
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
                        f"ETCD_LISTEN_PEER_URLS=http://0.0.0.0:2380",
                        f"ETCD_LISTEN_CLIENT_URLS=http://0.0.0.0:{self.etcd_client_port}",
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

        # update mao volumes based on ssh-dir conditional
        compose['services']['mao']['volumes'] += [f"{self.ssh_key_dir}:/home/user/.ssh"] if self.ssh_key_dir is not None else []

        return compose