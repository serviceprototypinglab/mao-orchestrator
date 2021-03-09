import yaml

class Installer:

    # installer settings
    install_dir = None
    workuser = None
    instance_ip = None
    etcd_operator_token = None

    def __init__(self):
        pass

    def run(self):
        """Runs the interactive installer CLI"""
        
        self.install_dir = input("Enter MAO install directory: ")
        self.workuser = input("Enter MAO workuser: ")
        self.instance_ip = input("Enter the public IP of the new MAO instance: ")
        self.etcd_operator_token = input("Enter the operator provided etcd token: ")

        print("MAO installer successfully finished!")

        print("Installer result: {}\n".format(self.__dict__))
        self._generate_compose()

    def _generate_compose(self):
        """Generate the Docker Compose YAML based on the user inputs"""

        # Python object representation of docker-compose.yaml
        compose = {
            "version": "3",
            "services": {
                "mao": {
                    "build": ".",
                    "environment": [
                        "workuser={}".format(self.workuser),
                        "etcdhost={}".format(self.instance_ip),
                        "importdir={}/data".format(self.install_dir)
                    ],
                    "ports": ["8080:8080"],
                    "volumes": [
                        "/var/run/docker.sock:/var/run/docker.sock"
                    ]
                }
            }
        }

        print(yaml.dump(compose))

