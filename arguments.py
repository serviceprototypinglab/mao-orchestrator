import argparse


class Arguments:
    def __init__(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(help="Available commands", dest='command')
        parser_tool = subparsers.add_parser('tool', help="List, register or run tools")
        tool_parsers = parser_tool.add_subparsers(help="Tool-related commands", dest="tool")
        # TODO: get tools
        get_tools = tool_parsers.add_parser('get', help="List tools")
        get_tools.add_argument('--name', help="Get details for tool")
        # TODO: register tool
        add_tools = tool_parsers.add_parser('add', help="Register a new tool")
        add_tools.add_argument('name', help="Name of the tool to register")
        add_tools.add_argument('author', help="Name of the author of the tool")
        add_tools.add_argument('image', help="Docker image with which to invoke the tool")
        add_tools.add_argument('data_repo', help="Associated data repository. Will be cloned on first invocation")
        add_tools.add_argument('code_repo', help="Code repository for the tool's source code")
        add_tools.add_argument('artefact', help="The type of artefact targeted by the tool")

        scheduled_tools = tool_parsers.add_parser('list-scheduled', help="List scheduled jobs")

        stop_tools = tool_parsers.add_parser('stop', help="Unschedule a tool")
        stop_tools.add_argument('id', help="ID of the tool to unschedule")

        remove_tools = tool_parsers.add_parser('remove', help="Unregister a tool")
        remove_tools.add_argument('name', help="Name of the tool to unregister")

        self.args = parser.parse_args()
