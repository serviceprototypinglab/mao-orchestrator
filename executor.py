from aiohttp import web
import json
import docker
import json


DOCKER_SOCKET_PATH = '/var/run/docker.sock'

app = web.Application()
routes = web.RouteTableDef()

docker_client = docker.from_env()

def pipeline_run(image, data_dir, env, cmd, docker_socket):
    print(f"Running image {image} with dir {data_dir}")
    _volumes = {data_dir: {'bind': '/usr/src/app/data'}}
    # bind docker sock if tool config requires it
    if docker_socket:
        _volumes[DOCKER_SOCKET_PATH] = {'bind': DOCKER_SOCKET_PATH}
    docker_client.containers.run(image,
                            volumes=_volumes,
                            network='host',
                            environment=env,
                            command=cmd,
                            auto_remove=True
                            )
    print("Done")
    return {"image_used": image, "data_dir": data_dir}

@routes.post('/run')
async def init(request):
    data = await request.json()
    image = data['image']
    data_dir = data['data_dir']
    env = data['env']
    cmd = data['cmd']
    docker_socket = data['docker_socket']
    response = pipeline_run(image, data_dir, env, cmd, docker_socket)
    return web.json_response(response)

app.add_routes(routes)
if __name__ == '__main__':
    web.run_app(app, port=8081)
