import configparser
import json
import schedule
from datetime import datetime
import os
import subprocess
from etcd_client import write, get
import sqlalchemy
from sqlalchemy import Table, Column, String, select, cast
from sqlalchemy.dialects.postgresql import JSONB

#logging.basicConfig(level=logging.DEBUG)
config = configparser.ConfigParser()
config.read('config.ini')
importdir = config['WORKING_ENVIRONMENT']['IMPORTDIR']
hostdir = config['WORKING_ENVIRONMENT']['HOSTDIR']

#### New pipeline: username is used to generate a name for the branch
user = config['WORKING_ENVIRONMENT']['USER']
if importdir.endswith('/'):
    importdir = importdir[:-1]

### PostgreSQL handling for pipeline store
psql_user = config['POSTGRES']['user']
psql_password = config['POSTGRES']['password']
psql_db = config['POSTGRES']['db']
psql_host = config['POSTGRES']['host']
psql_port = 5432
# connect to database
psql_url = f'postgresql://{psql_user}:{psql_password}@{psql_host}:{psql_port}/{psql_db}'
psql_con = sqlalchemy.create_engine(psql_url, client_encoding='utf8')
psql_meta = sqlalchemy.MetaData(bind=psql_con, reflect=True)
# create (if not exist) pipeline table
psql_pipeline = Table('pipelines', psql_meta,
    Column('name', String, primary_key=True),
    Column('content', JSONB),
    extend_existing=True
)
psql_meta.create_all(psql_con)

def list_jobs():
    return schedule.list_jobs()

def remove_job(id):
    return schedule.delete_job(id)

###### New pipeline methods ###################################################

def pipeline_init(tool, dataset, env=None, cmd=None):
    # Clone dataset
    ## Get git link
    dataset_json = get(f"dataset/{dataset}")
    ## etcd does not like double quotes but json needs them
    dataset_json = dataset_json.replace("'", '"')
    dataset_dict = json.loads(dataset_json)
    dataset_git = dataset_dict['master']
    local_dir = importdir + "/" + tool
    try:
        subprocess.run(f"git clone {dataset_git} {local_dir}", shell=True)
    except:
        return f"Could not clone, check if {local_dir} exists and is not empty"
    # Create new branch (use node name from config)
    branch_name = user
    ## Get into the git dir
    old_wd = os.getcwd()
    os.chdir(local_dir)
    try:
        subprocess.run(f"git checkout -b {branch_name}", shell=True)
        subprocess.run(f"git push --set-upstream origin {branch_name}", shell=True)
    except:
        return f"Could not create branch, check if {branch_name} already exists"
    os.chdir(old_wd)
    # Register the branch
    dataset_dict['nodes'].append(branch_name)
    write(f"dataset/{dataset}", dataset_dict)
    # Save the association tool + branch on node (including local path)
    pipeline = {
        "tool": tool,
        "dataset": dataset,
        "branch": branch_name,
        "local_dir": local_dir,
        "env": env,
        "cmd": cmd
        }
    
    # psql pipeline store
    _new_pipeline = psql_pipeline.insert().values(name=tool, content=pipeline)
    psql_con.execute(_new_pipeline)
    
    return pipeline

### Scheduling not supported yet
def pipeline_run(name, cron):
    # read config from psql pipeline store
    _query = select(
            [psql_pipeline.c.content]
        ).where(
            psql_pipeline.c.content['tool'] == cast(name, JSONB)
        )
    # only fetch one pipeline entry from psql as they have to be unique
    pipeline = psql_con.execute(_query).fetchone()[0]
    local_dir = pipeline['local_dir']
    host_dir = hostdir+ "/" + name
    tool_env = pipeline.get('env', None)
    tool_cmd = pipeline.get('cmd', None)
    # Run the tool + Mount the branch folder
    ## Fetch tool metadata from registry
    tool_json = get(f"tools/{name}")
    ## etcd does not like double quotes but json needs them
    tool_json = tool_json.replace("'", '"')
    tool_dict = json.loads(tool_json)
    tool_image = tool_dict['image']
    ## Use NEW run method from scheduler
    if cron == 'none':
        output = schedule.pipeline_run(tool_image, local_dir, host_dir, env=tool_env, cmd=tool_cmd)
        return {"pipeline": pipeline, "output": output}
    else:
        output = schedule.pipeline_cron(
            tool_image,
            local_dir,
            host_dir,
            cron,
            options={
                'env': tool_env,
                'cmd': tool_cmd
            } 
            )
        return {"pipeline": pipeline, "job_id": output}

###### End of new pipeline methods ############################################
