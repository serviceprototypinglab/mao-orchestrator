import requests
import configparser


config = configparser.ConfigParser()
config.read('join.ini')
gateway = config['GATEWAY']['IP']
username = input("Username: ")
ip = input("IP of the node: ")
location = input("Location of the node: ")
json_out = {
    "username": username,
    "ip": ip,
    "location": location
}
response = requests.post('http://{}:8081/register'.format(gateway),
                         json=json_out)
print(response.json())
