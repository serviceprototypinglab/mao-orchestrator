from aiohttp import web
import session
import random
import requests


app = web.Application()
routes = web.RouteTableDef()


@routes.post('/register')
async def register(request):
    data = await request.json()
    ips = session.get_ips()
    index = random.randint(0, len(ips) - 1)
    print(index)
    ip = ips[index]
    json_out = {
        "username": data['username'],
        "ip": data['ip'],
        "location": data['location']
    }
    response = requests.post('http://{}:8080/regnode'.format(ip),
                             json=json_out)
    session.create(data['username'], data['ip'], data['location'])
    return web.json_response(response.json())


@routes.post('/write')
async def register(request):
    data = await request.json()
    ips = session.get_ips()
    index = random.randint(0, len(ips) - 1)
    print(index)
    ip = ips[index]
    json_out = {
        "key": data['key'],
        "value": data['value']
    }
    response = requests.post('http://{}:8080/write'.format(ip),
                             json=json_out)
    return web.json_response(response.json())


@routes.post('/read')
async def register(request):
    data = await request.json()
    ips = session.get_ips()
    index = random.randint(0, len(ips) - 1)
    print(index)
    ip = ips[index]
    json_out = {
        "key": data['key']
    }
    response = requests.post('http://{}:8080/read'.format(ip),
                             json=json_out)
    return web.json_response(response.json())


@routes.post('/inspect')
async def register(request):
    data = await request.json()
    ips = session.get_ips()
    index = random.randint(0, len(ips) - 1)
    print(index)
    ip = ips[index]
    json_out = {
        "key": data['key']
    }
    response = requests.post('http://{}:8080/inspect'.format(ip),
                             json=json_out)
    return web.json_response(response.json())


app.add_routes(routes)
if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=8081)
