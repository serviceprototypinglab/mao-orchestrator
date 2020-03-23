import unittest
import requests
import json


def get_datasets():
    r = requests.get('http://0.0.0.0:8080/registry/datasets')
    return r.json()


def add_dataset(name, url):
    json_out = {
        "name": name,
        "url": url
    }
    r = requests.post('http://0.0.0.0:8080/registry/datasets', json=json_out)
    return r.json()


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
    return r.json()


def run_tool(name):
    json_out = {
        "name": name,
        "cron": False
    }
    r = requests.post('http://0.0.0.0:8080/jobs', json=json_out)
    return r.json()


class TestSpikeDetection(unittest.TestCase):
    def test_add_dataset(self):
        assert add_dataset('sar-static-data',
                       'https://github.com/EcePanos/sar-static-data.git') == 'https://github.com/EcePanos/sar-static-data.git'

    def test_get_datasets(self):
        assert get_datasets() == ['/data/sar-static-data']

    def test_add_tool(self):
        assert json.loads(add_tool('spike', 'panos', 'panosece/spike:latest', 'git@github.com:EcePanos/sar-static-data.git',
                                   'git@github.com:EcePanos/sar-static-data.git', 'testartefact')) == {"author": "panos",
                                                                                       "image": "panosece/spike:latest",
                                                                                       "data_repo": "git@github.com:EcePanos/sar-static-data.git",
                                                                                       "code_repo": "git@github.com:EcePanos/sar-static-data.git",
                                                                                       "artefact": "testartefact"}

    def test_run_tool(self):
        assert run_tool('spike')['tool'] == 'panosece/spike:latest'
