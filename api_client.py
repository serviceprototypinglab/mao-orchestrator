import collections
import requests
import json
from marshmallow import fields, EXCLUDE, Schema
from requests.exceptions import HTTPError

_URL = "http://127.0.0.1:8080"
_URL_TOOLS = "registry/tools"
_URL_DATASETS = "registry/datasets"
_URL_PIPELINE_REG = "registry/pipelines"
_URL_PIPELINE = "pipeline"
_URL_BARE = "bare-repo/init"

def _remove_prefix(path):
        """Removes prefixed from absolute etcd paths"""
        _result = path.split('/')
        _last_index = len(_result)-1
        return _result[_last_index]

class PipelineStep(Schema):
    name = fields.Str(required=True)
    tool = fields.Str(required=True)
    input_dataset = fields.Str(required=True, allow_none=True)
    output_dataset = fields.Str(required=True)
    cmd = fields.List(fields.Str, default=None, allow_none=True)
    env = fields.Dict(default=None, allow_none=True)
    docker_socket = fields.Bool(default=False)
    cron = fields.Str(load_only=True)

class Pipeline(Schema):

    PRIVATE_VARIABLE_PLACEHOLDER = "{{ MAO_PRIVATE_VARIABLE }}"

    name = fields.Str(required=True)
    steps = fields.List(fields.Nested(PipelineStep))
    instance_scheduled = fields.Bool(missing=False, load_only=True)
    federation_registered = fields.Bool(missing=False, load_only=True)

    @staticmethod
    def _api_get_pipelines():
        """Returns a list of pipelines registered with MAO from the API"""
        try:
            r = requests.get(f"{_URL}/{_URL_PIPELINE}")
            r.raise_for_status()
            _tools = r.json()
            return(_tools)
        except HTTPError as e:
            print(e)

    def update_fed_status(self):
        """Checks registration status of pipeline with federation registry"""
        try:
            r = requests.get(f"{_URL}/{_URL_PIPELINE_REG}/{self.name}")
            if r.status_code == 404:
                # pipeline not found in registry
                self.federation_registered = False
                return False
            elif r.status_code == 200:
                # pipeline found in registry
                self.federation_registered = True
                return True
            
            # check if any other error occurred
            r.raise_for_status()

        except HTTPError as e:
            print(e)

    def init(self):
        """Initialize new pipeline on MAO instance"""
        _pipeline = self.dump()
        try:
            r = requests.post(f"{_URL}/{_URL_PIPELINE}/init", json=_pipeline)
            r.raise_for_status()
            # update pipeline state
            self.update_fed_status()
            self.instance_scheduled = True
            return r.json()
        except HTTPError as e:
            _json = r.json()
            if _json.get('ok', None) != None:
                return _json
            print(e)

    def run(self, cron: str):
        """Run pipeline with specific cron configuration"""
        _pipeline = self.dump()
        try:
            r = requests.post(f"{_URL}/{_URL_PIPELINE}/run", json={
                "name": self.name,
                "cron": cron
            })
            r.raise_for_status()
        except HTTPError as e:
            print(e)

    def get_private_vars(self):
        _priv_vars = collections.defaultdict(dict)
        # iterate over all pipeline steps
        for step in self.steps:
            # check if step contains any environment definitions
            if step.env != None:
                for k, v in step.env.items():
                    if v == Pipeline.PRIVATE_VARIABLE_PLACEHOLDER:
                        _priv_vars[step.name][k] = ""
        return _priv_vars

    def set_private_vars(self, private_vars):
        for step in self.steps:
            if step.name in private_vars:
                for k, v in private_vars[step.name].items():
                    step.env[k] = v

    @classmethod
    def list(cls):
        """Returns a list of pipelines registered with instance"""
        pipelines = []
        _pipeline_data = cls._api_get_pipelines()
        for pipeline in _pipeline_data:
            _tmp_pipe = cls.load(pipeline, unknown=EXCLUDE)
            _tmp_pipe.update_fed_status()
            pipelines.append(_tmp_pipe)
        return pipelines

class Tool(Schema):
    name = fields.Str(required=True)
    image = fields.Str(required=True)
    author = fields.Str()
    # fields.Url does not work here for repo URL as we can also have SSH endpints
    # e.g. git@my.git-server.com/project1
    data_repo = fields.Str()
    code_repo = fields.Str()
    artefact = fields.Str()
    # TODO maybe remove load_only from description in future
    description = fields.Str(load_only=False)
    federation_registered = fields.Bool(missing=False, load_only=True)
    instance_scheduled = fields.Bool(missing=False, load_only=True)

    @staticmethod
    def _api_get_tools():
        """Returns a list of tools registered with MAO from the API"""
        try:
            r = requests.get(f"{_URL}/{_URL_TOOLS}")
            r.raise_for_status()
            _tools = r.json()
            _result = []
            for tool in _tools:
                _result.append(_remove_prefix(tool))
            return(_result)
        except HTTPError as e:
            print(e)

    @staticmethod
    def _api_get_tool(name: str):
        """Returns detailed configuration of a single MAO tool"""
        try:
            r = requests.get(f"{_URL}/{_URL_TOOLS}/{name}")
            r.raise_for_status()
            _tool = json.loads(r.json())
            return(_tool)
        except HTTPError as e:
            print(e)

    @classmethod
    def list(cls):
        """Returns a list of tools registered with MAO"""
        tools = []
        _tool_names = cls._api_get_tools()
        for tool_name in _tool_names:
            _result = cls._api_get_tool(tool_name)
            _result['name'] = tool_name
            tool = cls.load(_result)
            tools.append(tool)
        return tools

    def add(self):
        _tool = self.dump()
        try:
            r = requests.post(f"{_URL}/{_URL_TOOLS}", json=_tool)
            r.raise_for_status()
        except HTTPError as e:
            print(e)

class Dataset(Schema):
    name = fields.Str(required=True)
    master = fields.Str(required=True)
    nodes = fields.List(fields.Str(), required=True)

    @staticmethod
    def _api_get_dataset(name):
        """Returns detailed configuration of a single MAO dataset"""
        try:
            r = requests.get(f"{_URL}/{_URL_DATASETS}/{name}")
            r.raise_for_status()
            _dataset = json.loads(r.json())
            return(_dataset)
        except HTTPError as e:
            print(e)

    @staticmethod
    def _api_get_datasets():
        """Returns a list of datasets registered with MAO from the API"""
        try:
            r = requests.get(f"{_URL}/{_URL_DATASETS}")
            r.raise_for_status()
            _datasets = r.json()
            _result = []
            for dataset in _datasets:
                _result.append(_remove_prefix(dataset))
            return(_result)
        except HTTPError as e:
            print(e)
    
    @classmethod
    def list(cls):
        """Returns a list of datasets registered with MAO"""
        datasets = []
        _dataset_names = cls._api_get_datasets()
        for dataset_name in _dataset_names:
            _result = cls._api_get_dataset(dataset_name)
            _result['name'] = dataset_name
            dataset = cls.load(_result)
            datasets.append(dataset)
        return datasets

    def dump(self, *args, **kwargs):
        _partial = super(Dataset, self).dump(*args, **kwargs)
        _partial['body'] = {}
        _partial['body']['master'] = _partial.pop('master')
        _partial['body']['nodes'] = _partial.pop('nodes')
        return _partial

    def add(self):
        _dataset = self.dump()
        try:
            r = requests.post(f"{_URL}/{_URL_DATASETS}", json=_dataset)
            r.raise_for_status()
        except HTTPError as e:
            print(e)

class BareRepo(Schema):
    name = fields.Str(required=True)
    path = fields.Str(dump_only=True)

    @staticmethod
    def _api_init_bare(name):
        """Returns detailed configuration of a single MAO dataset"""
        try:
            r = requests.post(f"{_URL}/{_URL_BARE}", json={"name": name})
            r.raise_for_status()
            _bare = r.json()
            return _bare
        except HTTPError as e:
            print(e)
    
    def init(self):
        """Returns a list of datasets registered with MAO"""
        _result = self._api_init_bare(self.name)
        self.path = _result['path']
