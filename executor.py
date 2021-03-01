from aiohttp import web
import json
import docker
import json


app = web.Application()
routes = web.RouteTableDef()

docker_client = docker.from_env()

def pipeline_run(image, data_dir):
    docker_client.containers.run(image,
                             volumes={data_dir: {'bind': '/usr/src/app/data'},
                                    '/var/run/docker.sock':
                                    {'bind': '/var/run/docker.sock'},
                                   '/usr/bin/docker':
                                    {'bind': '/usr/bin/docker'}},
                             network='host')
    return "done"

@routes.post('/run')
async def init(request):
    data = await request.json()
    image = data['image']
    data_dir = data['data_dir']
    response = pipeline_run(image, data_dir)
    return web.json_response(response)

app.add_routes(routes)
if __name__ == '__main__':
    web.run_app(app, port=8081)
