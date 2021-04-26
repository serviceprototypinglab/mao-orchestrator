from aiohttp import web
import syncer
import etcd_client
import json
import schedule

app = web.Application()
routes = web.RouteTableDef()

@routes.get('/')
async def regtools(request):
    return web.json_response('hello')


@routes.get('/registry/tools')
async def regtools(request):
    return web.json_response(etcd_client.list('tools'))


@routes.get('/registry/tools/{tool}')
async def regtools(request):
    return web.json_response(etcd_client.get('tools/' + request.match_info['tool']))

@routes.get('/registry/datasets')
async def datasets(request):
    return web.json_response(etcd_client.list('dataset'))


@routes.get('/registry/datasets/{dataset}')
async def datasets(request):
    return web.json_response(etcd_client.get(f"dataset/{request.match_info['dataset']}/{request.match_info['node']}"))


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

# Register dataset with new schema
@routes.post('/registry/datasets')
async def register(request):
    data = await request.json()
    etcd_client.write("dataset/{}".format(data['name']), data['body'])
    return web.json_response(etcd_client.get("dataset/{}".format(data['name'])))

# Create the node branch, register and create pipeline config
@routes.post('/pipeline/init')
async def init(request):
    data = await request.json()
    tool = data['tool']
    dataset = data['dataset']
    env = data.get('env', None)
    cmd = data.get('cmd', None)
    docker_socket = data.get('docker_socket', False)
    response = syncer.pipeline_init(tool, dataset, env=env, cmd=cmd, docker_socket=docker_socket)
    return web.json_response(response)

# Run a pipeline (requires ssh configs in docker, WIP)
@routes.post('/pipeline/run')
async def init(request):
    data = await request.json()
    name = data['name']
    cron = 'none'
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
    return web.json_response(etcd_client.delete(f"dataset/{request.match_info['dataset']}/{request.match_info['node']}"))


@routes.delete('/jobs/{id}')
async def register(request):
    return web.json_response(syncer.remove_job(request.match_info['id']))

app.add_routes(routes)
if __name__ == '__main__':
    web.run_app(app)
