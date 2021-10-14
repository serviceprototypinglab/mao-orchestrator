from argparse import ArgumentParser, Namespace, _SubParsersAction


class Arguments:
    __parser: ArgumentParser
    __subparsers: _SubParsersAction

    def __init__(self) -> None:
        self.__parser = ArgumentParser()
        self.__subparsers = self.__parser.add_subparsers(help="Available commands", dest="command")
        self.__init__tool_parser()
        self.__init__instance_parser()
        self.__init__dataset_parser()
        self.__init__pipeline_parser()

    def __init__tool_parser(self) -> None:
        tool_parser: ArgumentParser = self.__subparsers.add_parser("tool", help="List, register or run tools")
        tool_subparsers: _SubParsersAction = tool_parser.add_subparsers(help="Tool-related commands", dest="tool")

        get_tools: ArgumentParser = tool_subparsers.add_parser("get", help="List tools")
        get_tools.add_argument("--name", help="Get details for tool. Omit to list all.")

        add_tools: ArgumentParser = tool_subparsers.add_parser("add", help="Register a new tool")
        add_tools.add_argument("--name", help="Name of the tool to register")
        add_tools.add_argument("--author", help="Name of the author of the tool")
        add_tools.add_argument("--image", help="Docker image with which to invoke the tool")
        add_tools.add_argument("--data_repo", help="Associated data repository. Will be cloned on first invocation")
        add_tools.add_argument("--code_repo", help="Code repository for the tool's source code")
        add_tools.add_argument("--artefact", help="The type of artefact targeted by the tool")

        tool_subparsers.add_parser("list-scheduled", help="List scheduled jobs")

        stop_tools: ArgumentParser = tool_subparsers.add_parser("stop", help="Unschedule a tool")
        stop_tools.add_argument("--id", help="ID of the tool to unschedule")

        remove_tools: ArgumentParser = tool_subparsers.add_parser("remove", help="Unregister a tool")
        remove_tools.add_argument("--name", help="Name of the tool to unregister")

    def __init__instance_parser(self) -> None:
        instance_parser: ArgumentParser = self.__subparsers.add_parser(
            "instance", help="Control MAO instance (e.g. install, init)"
        )
        instance_subparsers: _SubParsersAction = instance_parser.add_subparsers(
            help="Instance-related commands", dest="instance"
        )

        instance_subparsers.add_parser("install", help="Interactive MAO installer")
        instance_subparsers.add_parser("init", help="Initialize MAO instance (e.g. schedule tools)")

    def __init__dataset_parser(self) -> None:
        dataset_parser: ArgumentParser = self.__subparsers.add_parser(
            "dataset", help="Dataset related commands (e.g. get, add)"
        )
        dataset_subparsers: _SubParsersAction = dataset_parser.add_subparsers(
            help="Dataset related commands", dest="dataset"
        )

        dataset_get: ArgumentParser = dataset_subparsers.add_parser("get", help="Get list of registered datasets")
        dataset_get.add_argument("--name", help="Get details for dataset. Omit to list all.")

        dataset_add: ArgumentParser = dataset_subparsers.add_parser("add", help="Register new dataset")
        dataset_add.add_argument("--name", help="Name of the dataset to register")
        dataset_add.add_argument("--git_url", help="SSH git URL of the dataset to register")

        dataset_remove: ArgumentParser = dataset_subparsers.add_parser("remove", help="Delete a dataset")
        dataset_remove.add_argument("--name", help="Name of the dataset to delete")

    def __init__pipeline_parser(self) -> None:
        pipeline_parser: ArgumentParser = self.__subparsers.add_parser(
            "pipeline", help="Pipeline related commands (e.g. get)"
        )
        pipeline_subparsers: _SubParsersAction = pipeline_parser.add_subparsers(
            help="Pipeline related commands", dest="pipeline"
        )

        pipeline_get: ArgumentParser = pipeline_subparsers.add_parser("get", help="Get list of registered pipelines")
        pipeline_get.add_argument("--name", help="Get details for single pipeline")

        pipeline_subparsers.add_parser("add", help="Create a new pipeline")
        pipeline_run: ArgumentParser = pipeline_subparsers.add_parser("run", help="Run an initialized pipeline")
        pipeline_run.add_argument("--name", help="The identifier of the pipeline to run")
        # TODO(fix)
        # pipeline_run.add_argument("--cron", help="A cron expression to schedule the pipeline")

    def parse_args(self) -> Namespace:
        return self.__parser.parse_args()
