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
        # TODO: run/sechedule tool
        run_tools = tool_parsers.add_parser('run', help="Execute a tool immediately")
        run_tools.add_argument('name', help="Name of the tool to run")

        remove_tools = tool_parsers.add_parser('remove', help="Unregister a tool")
        remove_tools.add_argument('name', help="Name of the tool to unregister")

        schedule_tools = tool_parsers.add_parser('schedule', help="Schedule a tool to run periodically")
        schedule_tools.add_argument('name', help="Name of the tool to schedule")
        schedule_tools.add_argument('frequency', choices=['daily', 'weekly'], help="Execution schedule: daily/weekly")

        parser_dataset = subparsers.add_parser('dataset', help="List, register or retrieve dataset")
        dataset_parsers = parser_dataset.add_subparsers(help="Dataset-related commands", dest='dataset')
        # TODO: get datasets
        get_datasets = dataset_parsers.add_parser('get', help="List datasets")
        get_datasets.add_argument('--name', help="Get details for dataset")
        # TODO: register data
        add_datasets = dataset_parsers.add_parser('add', help="Register a new dataset")
        add_datasets.add_argument('name', help="Name of the dataset to register")
        add_datasets.add_argument('url', help="Github remote to clone the dataset")
        # TODO: retrieve data
        clone_datasets = dataset_parsers.add_parser('clone', help="Clone a dataset")
        clone_datasets.add_argument('name', help="Name of the dataset to retrieve")

        remove_dataset = dataset_parsers.add_parser('remove', help="Unregister a dataset")
        remove_dataset.add_argument('name', help="Name of the dataset to unregister")

        self.args = parser.parse_args()
        # TODO: change respones of all so that they send JSON objects to this
        # TODO: parse them and print output reports
