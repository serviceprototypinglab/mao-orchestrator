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
    Column('steps', JSONB),
    extend_existing=True
)
psql_meta.create_all(psql_con)

def list_jobs():
    return schedule.list_jobs()

def remove_job(id):
    return schedule.delete_job(id)

###### New pipeline methods ###################################################

def pipeline_list():
    # read from psql pipeline store
    _query = select(
            [psql_pipeline.c.options]
        )
    # only fetch one pipeline entry from psql as they have to be unique
    _pipelines = []
    _result = psql_con.execute(_query).fetchall()
    for pipeline in _result:
        print(pipeline)
        _pipelines.extend(pipeline)
    return _pipelines

def get_dataset(name):
    '''Returns dataset dict definition from federation etcd'''
    # get dataset from etcd
    dataset_json = get(f"dataset/{name}")
    dataset_json = dataset_json.replace("'", '"')
    dataset = json.loads(dataset_json)
    return dataset

def clone_git_repo(url, local_dir):
    try:
        subprocess.run(f"git clone {url} {local_dir}", shell=True)
    except:
        return f"Could not clone, check if {local_dir} exists and is not empty"

def init_dataset_repo(dataset_name, local_dir):
    # get input dataset from etcd
    input_dataset = get_dataset(dataset_name)
    # clone git repo
    clone_git_repo(input_dataset['master'], local_dir)

def create_step_branch(branch_name, local_dir):
    old_wd = os.getcwd()
    os.chdir(local_dir)
    try:
        subprocess.run(f"git checkout -b {branch_name}", shell=True)
        subprocess.run(f"git push --set-upstream origin {branch_name}", shell=True)
    except:
        return f"Could not create branch, check if {branch_name} already exists"
    os.chdir(old_wd)

def dataset_register_branch(dataset_name, branch):
    dataset = get_dataset(dataset_name)
    nodes = dataset['nodes']
    # only add branch if not already existing
    if branch not in nodes:
        nodes.append(branch)
        dataset['nodes'] = nodes
        write(f"dataset/{dataset_name}", dataset)

###### New pipeline methods ###################################################

def pipeline_init(name, steps):
    '''Initializes new MAO pipeline'''
    
    for step in steps:
        pipeline_step_init(step)

    # psql pipeline store
    _new_pipeline = psql_pipeline.insert().values(name=name, steps=steps)
    psql_con.execute(_new_pipeline)

    return {'name': name, 'steps': steps}

def pipeline_step_init(step):
    '''Initializes a single MAO pipeline step'''

    # prepare input dataset, if defined
    if step['input_dataset'] != None:
        input_dataset_name = step['input_dataset']
        input_dataset_path = f'{importdir}/{input_dataset_name}'
        input_dataset_branch = f"{step['name']}-{user}"
        init_dataset_repo(input_dataset_name, input_dataset_path)
        create_step_branch(input_dataset_branch, input_dataset_path)
        dataset_register_branch(input_dataset_name, input_dataset_branch)

        # update step dict
        step['input_dataset'] = {}
        step['input_dataset']['name'] = input_dataset_name
        step['input_dataset']['branch'] = input_dataset_branch


    # prepare output dataset
    output_dataset_name = step['output_dataset']
    output_dataset_path = f'{importdir}/{output_dataset_name}'
    output_dataset_branch = f"{step['name']}-{user}"
    init_dataset_repo(output_dataset_name, output_dataset_path)
    create_step_branch(output_dataset_branch, output_dataset_path)
    dataset_register_branch(output_dataset_name, output_dataset_branch)

    # update step dict
    step['output_dataset'] = {}
    step['output_dataset']['name'] = output_dataset_name
    step['output_dataset']['branch'] = output_dataset_branch

    return step

### Scheduling not supported yet
def pipeline_run(name, cron):
    # read config from psql pipeline store
    _query = select(
            [psql_pipeline.c.steps]
        ).where(
            psql_pipeline.c.name == name
        )
    # only fetch one pipeline entry from psql as they have to be unique
    steps = psql_con.execute(_query).fetchone()[0]
    # local_dir = pipeline['local_dir']
    # host_dir = hostdir+ "/" + name
    # tool_env = pipeline.get('env', None)
    # tool_cmd = pipeline.get('cmd', None)
    # tool_docker_socket = pipeline.get('docker_socket', False)
    # # Run the tool + Mount the branch folder
    # ## Fetch tool metadata from registry
    # tool_json = get(f"tools/{name}")
    # ## etcd does not like double quotes but json needs them
    # tool_json = tool_json.replace("'", '"')
    # tool_dict = json.loads(tool_json)
    # tool_image = tool_dict['image']
    ## Use NEW run method from scheduler
    if cron is None:
        output = schedule.pipeline_run(importdir, hostdir, steps)
        return {"pipeline": name, "output": output}
    else:
        # output = schedule.pipeline_cron(
        #     tool_image,
        #     local_dir,
        #     host_dir,
        #     cron,
        #     options={
        #         'env': tool_env,
        #         'cmd': tool_cmd,
        #         'docker_socket': tool_docker_socket
        #     } 
        #     )
        return {"pipeline": pipeline, "job_id": output}

###### End of new pipeline methods ############################################
