from aiohttp import web
import syncer
from ruamel.yaml import YAML


app = web.Application()
routes = web.RouteTableDef()
yaml = YAML()
yaml.preserve_quotes = True


@routes.get('/regtools')
async def regtools(request):
    return web.json_response(syncer.list('tools'))


@routes.get('/datasets')
async def datasets(request):
    return web.json_response(syncer.list('data'))


@routes.post('/register')
async def register(request):
    data = await request.json()
    syncer.write("tools/{}".format(data['name']), data['url'])
    return web.json_response(syncer.get("tools/{}".format(data['name'])))


@routes.post('/regdata')
async def register(request):
    data = await request.json()
    syncer.write("data/{}".format(data['name']), data['url'])
    return web.json_response(syncer.get("data/{}".format(data['name'])))


@routes.post('/help')
async def help(request):
    query = await request.json()
    with open('local.yml', 'r') as local:
        data = yaml.load(local)
    for program in data['Programs']:
        if program['Name'] == (query['name']):
            return web.json_response(program['Commands'])
    else:
        return web.json_response("No such program")


@routes.post('/retrieve')
async def retrieve(request):
    data = await request.json()
    syncer.retrieve(data['name'])
    return web.json_response("Done")


@routes.post("/run")
async def run(request):
    data = await request.json()
    print(data)
    syncer.sync(data)
    return web.json_response("Done")


app.add_routes(routes)
if __name__ == '__main__':
    web.run_app(app)
