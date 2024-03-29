# Tools and Jobs

The primary function of the orchestrator is to manage the tools of the MAO project and allow its members to execute them on premises with minimal setup overhead.

A tool is developed as a Docker image that complies to the basic guidelines in the main README. It must be deployed to a public Docker registry so that it can be used by anyone and finally it must be registered into the etcd cluster to make itself known to the system.

The following CLI instructions perform these functionalities.

## Managing the tool registry

### The tool registry format

A registry entry for a tool is a key/value pair where the name of the tool is the key and the value is a JSON string with the following properties:
```
{
  "name": "valid_identifier",
  "author": "Panos",
  "image": "panos/testtool",
  "data_repo": "https://github.com/foo/bar",
  "code_repo": "https://github.com/foo/bardata",
  "artefact": "docker_images",
  "description": "An example tool entry"
}
```
The `image` and `data_repo` attributes are necessary to execute an image properly.

The orchestrator uses the `image` to execute the tool, and before the first execution clones the `data_repo` to mount it as the data volume to the container.

##### Note:
Pushing to and merging repos is NOT handled by the orchestrator. This has to be done manually to ensure proper handling of conflicts. The peer-based auditing tools provided by the orchestrator can help to resolve conflicts, but should not be viewed as a be-all-end-all solution.

### Getting information

You can list the available tools or get information on a specific tool.
#### CLI
```
python maoctl.py tool get
```
```
python maoctl.py tool get --name NAME
```

### Adding a tool to the registry

Register a tool to the registry. Ensure the tool `image` can be pulled by any user and that the `data_repo` can be cloned and pulled from by any user.
#### CLI
```
python maoctl.py tool add 
 --name NAME \ 
 --author AUTHOR \ 
 --image IMAGE \ 
 --data_repo DATA_REPO \ 
 --code_repo CODE_REPO \ 
 --artefact ARTEFACT
```
### Removing a tool from the registry

Removes the specified tool from the registry.
#### CLI
```
python maoctl.py tool remove --name NAME
```
## Managing jobs

Jobs are handled by an APScheduler asyncio process pool instance with a PostgreSQL back-end. They can be run immediately or be scheduled to run daily or weekly.

##### Note:
Check the advanced section if you wish to use crontab-like syntax.

### List pending jobs
List the currently scheduled jobs. This will also display information on the listener jobs that are spawned automatically when the orchestrator starts.
#### CLI
```
python maoctl.py tool list-scheduled
```
### Run a tool immediately
*currently unsupported*

Run a tool right away and display a short summary. For the summary to work the tool must be compliant with the spike detector.
#### CLI
```
python maoctl.py tool run <name>
```
#### Sample report
```
Report:
Tool image: panosece/spike:latest
Data directory: /home/panos/testconfig/spike
Message to scheduler: {"container": "panosece/spike:latest", "tool": "spike", "dataset": "/home/panos/testconfig/spike", "cron": false}
Scheduler output:
Tool image: panosece/spike:latest
Name of tool: spike
Data directory: /home/panos/testconfig/spike
Spike detector output:
Data directory: /home/panos/testconfig/spike
Number of data snapshots: 9
Current rolling average of control metric: 900.0
Value of control metric in current snapshot: 900
Difference:0.0
Gain:0.0%
No data anomalies detected
```
### Schedule a tool
*currently unsupported*

Schedule the tool to run periodically. Daily and weekly execution is supported.
#### CLI
```
python maoctl.py tool schedule <name> {daily,weekly}
```
### Remove a job from the schedule
A scheduled tool can also be un-scheduled.
#### CLI
```
python maoctl.py tool stop --id ID
```
## Advanced
### Custom Docker parameters
You can specify a command to run inside the tool container and a set of environment variables by setting the optional `command` (list) and `env` (dict) parameters respectively in the run/schedule request. This is possible **only** via the API. The CLI currently leaves these parametars empty
### Crontab syntax for scheduler
*set as NULL for now as it breaks*

You can use crontab syntax for the frequency parameter of the scheduler request. This is possible both through the CLI and API.
