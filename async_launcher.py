import json

from aiohttp import web

import etcd_client
import syncer

app = web.Application()
routes = web.RouteTableDef()

@routes.get('/')
async def regtools(request):
    return web.json_response('hello')


@routes.get('/registry/tools')
async def regtools(request):
    _tools = etcd_client.list('tools')
    # remove '/tools/' prefix form etcd return values
    for i, tool in enumerate(_tools):
        _tools[i] = tool.replace("/tools/", "")
    return web.json_response(_tools)


@routes.get('/registry/tools/{tool}')
async def regtools(request):
    try: 
        t = etcd_client.get('tools/' + request.match_info['tool'])
        return web.json_response(t)
    except Exception:
        raise web.HTTPNotFound(reason="Tool not found")

@routes.get('/registry/datasets')
async def datasets(request):
    _datasets = etcd_client.list('dataset')
    # remove '/dataset/' prefix form etcd return values
    for i, dataset in enumerate(_datasets):
        _datasets[i] = dataset.replace("/dataset/", "")
    return web.json_response(_datasets)


@routes.get('/registry/datasets/{dataset}')
async def datasets(request: web.Request):
    try:
        d = etcd_client.get(f"dataset/{request.match_info['dataset']}")
        return web.json_response(d)
    except Exception:
        raise web.HTTPNotFound(reason="Dataset not found")


@routes.get('/jobs')
async def datasets(request):
    return web.json_response(syncer.list_jobs())

@routes.post('/write')
async def write(request):
    data = await request.json()
    etcd_client.write('raw/' + data['key'], data['value'], ephemeral=True)
    return web.json_response(etcd_client.get('raw/' + data['key']))

@routes.post('/read')
async def write(request):
    data = await request.json()
    return web.json_response(json.loads(etcd_client.get(data['key'])))

@routes.post('/inspect')
async def write(request):
    data = await request.json()
    return web.json_response(etcd_client.read_recursive(data['key']))

@routes.post('/registry/tools')
async def register(request):
    data = await request.json()
    etcd_client.write("tools/{}".format(data['name']),
                    '{{"author":"{}",\
"image":"{}",\
"data_repo":"{}",\
"code_repo":"{}",\
"artefact":"{}"}}'
                       .format(data['author'], data['image'],
                               data['data_repo'], data['code_repo'],
                               data['artefact']))
    return web.json_response(etcd_client.get("tools/{}".format(data['name'])))

##### New pipeline endpoints ##################################################

# Get pipeline from MAO registry
@routes.get('/registry/pipelines/{pipeline}')
async def write(request):
    _result = syncer.pipeline_get(request.match_info['pipeline'])
    if _result is None:
        return web.json_response({"error": "Pipeline not found in registry"}, status=404)
    return web.json_response(_result)

# Register dataset with new schema
@routes.post('/registry/datasets')
async def register(request):
    data = await request.json()
    # TODO check with Panos: quotes handling inside etcd
    body = json.dumps(data['body'])
    etcd_client.write("dataset/{}".format(data['name']), body)
    return web.json_response(etcd_client.get("dataset/{}".format(data['name'])))

# Get list of currently registered pipelines
@routes.get('/pipeline')
async def init(request):
    _pipelines = syncer.pipeline_list()
    return web.json_response(_pipelines)

# Create the node branch, register and create pipeline config
# TODO: [Pipeline] maybe switch to /pipeline?
@routes.post('/pipeline/init')
async def init(request):
    data = await request.json()
    status = 200
    response = syncer.pipeline_init(data['name'], data['steps'])
    if not response['ok']:
        status = 400
    return web.json_response(response, status=status)

# Run a pipeline (requires ssh configs in docker, WIP)
@routes.post('/pipeline/run')
async def init(request):
    data = await request.json()
    name = data['name']
    cron = None
    if 'cron' in data:
        cron = data['cron']
    response = syncer.pipeline_run(name, cron)
    return web.json_response(response)

####### End of new pipeline endpoints #########################################

@routes.delete('/registry/tools/{tool}')
async def register(request):
    return web.json_response(etcd_client.delete("tools/{}".format(request.match_info['tool'])))

@routes.delete('/registry/datasets/{dataset}')
async def register(request):
    return web.json_response(etcd_client.delete(f"dataset/{request.match_info['dataset']}"))


@routes.delete('/jobs/{id}')
async def register(request):
    return web.json_response(syncer.remove_job(request.match_info['id']))

# Create a local bare repository
@routes.post('/bare-repo/init')
async def init(request):
    data = await request.json()
    response = syncer.bare_repo_init(data['name'])
    return web.json_response(response)

app.add_routes(routes)
if __name__ == '__main__':
    web.run_app(app)
