# MAO-MAO-Framework

MAO-MAO collaborative research framework. Allows scheduled execution of periodic data collectors and has built-in spike detection for the data.
This implementation makes use of an etcd cluster for member discovery, persistence and metadata sharing and a simple git interface for cloning data sets.

## Install instructions

- Install etcd and start a cluster (or join the production cluster once it exists)
```
sudo apt install etcd-server
etcd
```
- Setup your importdir and etcd settings in config.ini . Importdir is where your local data will be stored.
- `pip3 install -r requirements.txt`

#### Start here if using the demo VM.
To launch the framework:
```
python3 async_launcher.py
```
At this stage it runs in the foreground so you will need a new terminal.

Launch the scheduler:
```
python3 schedule.py
```
At this stage it also runs on the foreground so you will need yet another terminal. Also, this is where the spike detector will write its output.

#### To add a new tool:
- First dockerize it using the guidelines (coming soon!) for now, you can do
```
docker build --tag=<name-docker-image> .
```
Inside this directory to build the dummy tool. **Keep the name of the generated image handy.**

- Register the tool:

 ```
 curl -d '{"name":"dummy", "url":"<name-docker-image>"}' -H "Content-Type: application/json" -X POST http://0.0.0.0:8080/register
 ```

## Running experiments
- Request a run:
```
curl -d '{"name":"dummy", "dataset":"none", "cron":false}' -H "Content-Type: application/json" -X POST http://0.0.0.0:8080/run
```
This will make the tool run immediately.

- Schedule a run:
```
curl -d '{"name":"dummy", "dataset":"none", "cron":true, "frequency":"<daily/weekly>"}' -H "Content-Type: application/json" -X POST http://0.0.0.0:8080/run
```
This will make the scheduler run the program once a day or week. It will coalesce and retry failed jobs but at this stage has NO persistence.

## Roadmap

- git integration with automated key management for automatically updating datasets
- notification service for spike detection based on etcd listeners
- daemonisation and better I/O
- a CLI client to negate the need for raw HTTP requests
- scheduler persistence
