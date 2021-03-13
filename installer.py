import yaml
import secrets
import string

from pathlib import Path
from shutil import which

class Installer:

    # MAO orchestrator dependencies
    dependencies = ['docker', 'docker-compose']

    def __init__(self):
        pass

    def run(self):
        """Runs the interactive installer CLI"""

        # check if all dependencies are installed
        _dep_installed, _dep_name = self._check_dependencies()
        if _dep_installed == False:
            print("[Error] Missing MAO orchestrator dependency: {}".format(_dep_name))
            exit(1)
        
        self.install_dir = input("Enter MAO install directory: ")
        self.workuser = input("Enter MAO workuser: ")
        self.instance_ip = input("Enter the public IP of the new MAO instance: ")
        self.etcd_operator_input = input("Enter the operator provided etcd config: ")
        self.git_email = input("Enter your git config email address: ")
        self.git_name = input("Enter your git config name: ")
        self.ssh_key_dir = input("Enter directory with ssh keys: ")

        # auto generated parameters
        _alphabet = string.ascii_letters + string.digits
        self.scheduler_pw = ''.join(secrets.choice(_alphabet) for i in range(20))
        self.scheduler_db = "schedule"
        self.import_dir = "/home/user/data"
        self.etcd_client_port = "2379"

        # create MAO install directory
        try:
            Path(self.install_dir).mkdir(parents=True, exist_ok=True)
        except PermissionError:
            print("[Error] Permission to create directory '{}' denied.".format(self.install_dir))
            exit(1)

        # write generated docker-compose.yaml to install directory
        with open("{}/docker-compose.yaml".format(self.install_dir), 'w') as file:
            yaml.dump(self._generate_compose(), file)

        print("\nMAO installer successfully finished!")
        print("\nUse the following commands to get your MAO instance up and running:")
        print("\t$ cd {}".format(self.install_dir))
        print("\t$ docker-compose up")

    def _check_dependencies(self):

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
                    "build": ".",
                    "environment": [
                        "importdir={}".format(self.import_dir),
                        "hostdir={}/data".format(self.install_dir),
                        "workuser={}".format(self.workuser),
                        "etcdhost={}".format(self.instance_ip),
                        # TODO maybe witch to more speaking var names e.g. etcd_port?
                        "port={}".format(self.etcd_client_port),
                        "dbuser={}".format(self.scheduler_db),
                        "password={}".format(self.scheduler_pw),
                        "db={}".format(self.scheduler_db),
                        "dbhost=127.0.0.1",
                        "gitemail={}".format(self.git_email),
                        "gitusername={}".format(self.git_name)
                    ],
                    "ports": ["8080:8080"],
                    "volumes": [
                        # mount data directory from host
                        "{host_dir}:{container_dir}".format(
                            host_dir=self.install_dir,
                            container_dir=self.import_dir
                        ),
                        # mount git used ssh keys directory
                        "{}:/home/user/.ssh".format(self.ssh_key_dir)
                    ],
                    "network_mode": "host",
                    "depends_on": [
                        "etcd",
                        "db"
                    ]
                },
                # MAO tool executor
                "executor": {
                    "build": ".",
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
                        "POSTGRES_DB={}".format(self.scheduler_db),
                        "POSTGRES_PASSWORD={}".format(self.scheduler_pw),
                        "POSTGRES_USER={}".format(self.scheduler_db)
                    ],
                    "volumes": [
                        # mount postgresql data directory
                        "{}/psql:/var/lib/postgresql/data".format(self.install_dir)
                    ],
                    "network_mode": "host"
                },
                # MAO etcd distributed k/v store
                "etcd": {
                    "image": "quay.io/coreos/etcd:v3.4.15",
                    "environment": [
                        "ALLOW_NONE_AUTHENTICATION=yes",
                        "ETCD_NAME={}".format(self.git_name),
                        "ETCD_DATA_DIR=/etcd-data",
                        "ETCD_INITIAL_ADVERTISE_PEER_URLS=http://{}:2380".format(self.instance_ip),
                        "ETCD_LISTEN_PEER_URLS=http://{}:2380".format(self.instance_ip),
                        "ETCD_LISTEN_CLIENT_URLS=http://{pub_ip}:{port}".format(
                            pub_ip=self.instance_ip,
                            port=self.etcd_client_port
                        ),
                        "ETCD_ADVERTISE_CLIENT_URLS=http://{pub_ip}:{port}".format(
                            pub_ip=self.instance_ip,
                            port=self.etcd_client_port
                        ),
                        #"ETCD_INITIAL_CLUSTER_TOKEN=etcd-cluster",
                        "ETCD_INITIAL_CLUSTER_STATE=existing",
                        "ETCD_INITIAL_CLUSTER={}".format(self.etcd_operator_input)
                    ],
                    "volumes": [
                        # mount etcd data directory
                        "{}/etcd:/etcd-data".format(self.install_dir)
                    ],
                    "network_mode": "host"
                }
            }
        }

        return compose