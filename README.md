# MAO-MAO-Framework

MAO-MAO collaborative research framework.

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

#### To add a new tool:
- First dockerize it using the guidelines (coming soon!) for now, you can do
```
docker build .
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
