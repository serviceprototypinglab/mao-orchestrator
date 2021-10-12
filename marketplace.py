import requests
from marshmallow import fields
from marshmallow.schema import Schema

import api_client as MaoClient

_URL = "https://mao-mao-research.github.io/hub/api"
# local mock URL for development
# use 'serve_local_marketplace.sh' in the /mocks directory to use local marketplace data
#_URL = "http://127.0.0.1:8333/"
_URL_TOOLS = "tools.json"
_URL_FEDERATIONS = "federations.json"
_URL_PIPELINES = "pipelines.json"

class MarketplaceNotReachable(Exception):
    pass

class Federation(Schema):
    name = fields.Str(required=True)
    description = fields.Str(required=True)
    contacts = fields.List(fields.Email(), required=True)

    @staticmethod
    def _get_federations():
        """Retrieves federations from MAO marketplace"""

        _response = requests.get(f'{_URL}/{_URL_FEDERATIONS}')
        if not _response.ok:
            raise MarketplaceNotReachable(
                ("Fetching tools form marketplace failed, "
                f"check if your instance can reach {_URL}/{_URL_FEDERATIONS}")
                )

        _federations = _response.json()
        return _federations

    @classmethod
    def list(cls):
        market = cls._get_federations()
        federations = []
        for fed in market:
            federations.append(Federation.load(fed))
        return federations

class Tool(MaoClient.Tool):

    @staticmethod
    def _api_get_tool(name: str):
        raise NotImplementedError

    @staticmethod
    def _api_get_tools():
        """Retrieves federations from MAO marketplace"""

        _response = requests.get(f'{_URL}/{_URL_TOOLS}')
        if not _response.ok:
            raise MarketplaceNotReachable(
                ("Fetching tools form marketplace failed, "
                f"check if your instance can reach {_URL}/{_URL_TOOLS}")
                )

        _tools = _response.json()
        return _tools

    @classmethod
    def list(cls):
        """Returns a list of tools available in the MAO marketplace"""
        tools = []
        _tools_json = cls._api_get_tools()
        for tool in _tools_json:
            tool = cls.load(tool)
            tools.append(tool)
        return tools

class Pipeline(MaoClient.Pipeline):
    description = fields.Str(required=True, load_only=True)

    @staticmethod
    def _api_get_pipelines():
        """Retrieves pipelines from MAO marketplace"""
        _response = requests.get(f'{_URL}/{_URL_PIPELINES}')
        if not _response.ok:
            raise MarketplaceNotReachable(
                ("Fetching pipelines form marketplace failed, "
                f"check if your instance can reach {_URL}/{_URL_PIPELINES}")
                )

        _pipelines = _response.json()
        return _pipelines
