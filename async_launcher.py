from aiohttp import web
import syncer
import etcd_client
import json


app = web.Application()
routes = web.RouteTableDef()


@routes.get('/registry/tools')
async def regtools(request):
    return web.json_response(etcd_client.list('tools'))


@routes.get('/registry/tools/{tool}')
async def regtools(request):
    return web.json_response(etcd_client.get('tools/' + request.match_info['tool']))


@routes.get('/registry/datasets')
async def datasets(request):
    return web.json_response(etcd_client.list('data'))


@routes.get('/registry/datasets/{dataset}/{node}')
async def datasets(request):
    return web.json_response(etcd_client.get(f"data/{request.match_info['dataset']}/{request.match_info['node']}"))


@routes.get('/registry/datasets/{dataset}')
async def datasets(request):
    return web.json_response(etcd_client.read_recursive(f"data/{request.match_info['dataset']}"))


@routes.get('/files')
async def datasets(request):
    return web.json_response(syncer.list_local())


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


@routes.post('/registry/datasets')
async def register(request):
    data = await request.json()
    etcd_client.write("data/{}/{}".format(data['name'], data['node']), data['url'])
    return web.json_response(etcd_client.get("data/{}".format(data['name'])))


@routes.delete('/registry/tools/{tool}')
async def register(request):
    return web.json_response(etcd_client.delete("tools/{}".format(request.match_info['tool'])))


@routes.delete('/registry/datasets/{dataset}/{node}')
async def register(request):
    return web.json_response(etcd_client.delete(f"data/{request.match_info['dataset']}/{request.match_info['node']}"))


@routes.delete('/jobs/{id}')
async def register(request):
    return web.json_response(syncer.remove_job(request.match_info['id']))


@routes.delete('/files/{name}')
async def register(request):
    return web.json_response(syncer.remove_local(request.match_info['name']))


@routes.get('/files/clone/{dataset}/{node}')
async def retrieve(request):
    dataset = request.match_info['dataset']
    node = request.match_info['node']
    response = syncer.retrieve(dataset, node)
    return web.json_response(response)


@routes.get('/files/cloneall/{dataset}')
async def retrieveall(request):
    reg = etcd_client.read_recursive(f"data/{request.match_info['dataset']}")
    nodes = list(key.split('/')[3] for key in reg.keys())
    response = syncer.temp_retrieve(request.match_info['dataset'], nodes)
    return web.json_response(response)


@routes.post("/jobs")
async def run(request):
    data = await request.json()
    print(data)
    response = syncer.sync(data)
    return web.json_response(response)


app.add_routes(routes)
if __name__ == '__main__':
    web.run_app(app)
