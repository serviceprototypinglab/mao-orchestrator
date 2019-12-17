from aiohttp import web
import syncer
import json


app = web.Application()
routes = web.RouteTableDef()


@routes.get('/regtools')
async def regtools(request):
    return web.json_response(syncer.list('tools'))


@routes.get('/regtools/{tool}')
async def regtools(request):
    return web.json_response(syncer.get('tools/' + request.match_info['tool']))


@routes.get('/datasets')
async def datasets(request):
    return web.json_response(syncer.list('data'))


@routes.get('/datasets/{dataset}')
async def datasets(request):
    return web.json_response(syncer.get('data/' + request.match_info['dataset']))


@routes.get('/locallist')
async def datasets(request):
    return web.json_response(syncer.list_local())


@routes.get('/jobslist')
async def datasets(request):
    return web.json_response(syncer.list_jobs())

@routes.post('/write')
async def write(request):
    data = await request.json()
    syncer.write('raw/' + data['key'], data['value'], ephemeral=True)
    return web.json_response(syncer.get('raw/' + data['key']))

@routes.post('/read')
async def write(request):
    data = await request.json()
    return web.json_response(json.loads(syncer.get(data['key'])))

@routes.post('/register')
async def register(request):
    data = await request.json()
    syncer.write("tools/{}".format(data['name']),
                    '{{"author":"{}",\
"image":"{}",\
"data_repo":"{}",\
"code_repo":"{}",\
"artefact":"{}"}}'
                       .format(data['author'], data['image'],
                               data['data_repo'], data['code_repo'],
                               data['artefact']))
    return web.json_response(syncer.get("tools/{}".format(data['name'])))


@routes.post('/regdata')
async def register(request):
    data = await request.json()
    syncer.write("data/{}".format(data['name']), data['url'])
    return web.json_response(syncer.get("data/{}".format(data['name'])))


@routes.post('/tooldelete')
async def register(request):
    data = await request.json()
    return web.json_response(syncer.delete("tools/{}".format(data['name'])))


@routes.post('/datadelete')
async def register(request):
    data = await request.json()
    return web.json_response(syncer.delete("data/{}".format(data['name'])))


@routes.post('/jobdelete')
async def register(request):
    data = await request.json()
    return web.json_response(syncer.remove_job(data['id']))


@routes.post('/localdelete')
async def register(request):
    data = await request.json()
    return web.json_response(syncer.remove_local(data['name']))


@routes.post('/audit')
async def register(request):
    data = await request.json()
    return web.json_response(syncer.create_audit(data['name']))


@routes.post('/retrieve')
async def retrieve(request):
    data = await request.json()
    response = syncer.retrieve(data['name'])
    return web.json_response(response)


@routes.post("/run")
async def run(request):
    data = await request.json()
    print(data)
    response = syncer.sync(data)
    return web.json_response(response)


app.add_routes(routes)
if __name__ == '__main__':
    web.run_app(app)
