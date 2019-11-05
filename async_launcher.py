from aiohttp import web
import syncer


app = web.Application()
routes = web.RouteTableDef()


@routes.get('/regtools')
async def regtools(request):
    return web.json_response(syncer.list('tools'))


@routes.get('/datasets')
async def datasets(request):
    return web.json_response(syncer.list('data'))


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
