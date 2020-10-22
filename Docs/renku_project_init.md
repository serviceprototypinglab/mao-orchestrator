# Initial setup of MAO-Renku pipeline

## Data acquisition with MAO

- Begin by setting up a MAO-compatible data acquisition tool as per the [guidelines](https://github.com/serviceprototypinglab/mao-orchestrator).

- Register the tool to MAO according to the steps [here](https://github.com/serviceprototypinglab/mao-orchestrator/blob/master/Docs/Tools.md)

## Initial setup of Renku project and workflow

- Create a Renku project and manually import a few data samples retrieved from your data tool.

- Create the Renku reproducible workflow.

## Automation

- Register the Renku repo with the cluster.

```
python3 maoctl.py data add <parent-dataset-name> <your-node-name> <git-link>
```

- Run the tool using the `--renku` flag, and include the new Renku project in the optional arguments

eg
```
python3 maoctl.py tool run <your-tool> --renku --dataset <parent-dataset-name> --node <your-node-name>
```

After the tool executes the new raw data will be pushed to Renku and ```renku update``` will be invoked. If this step is successfull you should see new output data in the Renku repository.

## Troubleshooting

#### Problem: No data generated

- Ensure the MAO config.ini file is configured properly, and your datadir is populated when a tool is run (with or withour Renku).

- Ensure your host is properly configured to clone/push from/to Renku over SSH. If needed confirm these actions manually.

#### Problem: Data is pushed and update is invoked, but no new output generated

- Ensure the Renku workflow you have recorded detects which files to use as input. This can be tested by manually adding new inputs and invoking ```renku update```, either on a host with Renku CLI installed or in a Renku interactive environment. The most reliable way to ensure this works is to set the input/output parameters for all `renku run` commands as per the Renku [cheatsheet](https://raw.githubusercontent.com/SwissDataScienceCenter/renku/master/docs/_static/cheatsheet/cheatsheet.pdf).

## Data acquisition test-run and clean up

- For the trial run you can use mock values for the repository fields, as they will be replaced by Renku repos. Pay special attention that the data files are indeed generated on the host, as this is the most common point of failure.

- Send a DELETE request to `localhost:8080/files/{your-tool}` to clean up the local files and configuration entries of the test run.

## Renku workflow test-run

To ensure the automated workflow will work as expected, you can try to clone the repo, add some more data, and invoke `renku update` using the CLI. These are the same steps run by the automated update feature.
