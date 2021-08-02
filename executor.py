from aiohttp import web
import json
import docker
import json
import subprocess
from docker import errors


DOCKER_SOCKET_PATH = '/var/run/docker.sock'
OUTPUT_UID = 1000

app = web.Application()
routes = web.RouteTableDef()

docker_client = docker.from_env()

def chown_output(uid, dir):
    # spawn a busybox with output repo mounted to adjust the file permissions
    docker_client.containers.run("busybox:latest",
                            volumes={dir: {'bind': '/usr/src/app/data'}},
                            command=["/bin/sh", "-c", f"chown -R {uid}:{uid} /usr/src/app/data && sleep 1"],
                            auto_remove=True
                            )

def pipeline_run(image, input_dir, output_dir, env, cmd, docker_socket):
    print(f"Running image {image} with input_dir {input_dir} and output_dir {output_dir}")
    _volumes = {output_dir: {'bind': '/usr/src/app/data'}}
    # bind docker sock if tool config requires it
    if docker_socket:
        _volumes[DOCKER_SOCKET_PATH] = {'bind': DOCKER_SOCKET_PATH}
    if input_dir is not None:
        _volumes[input_dir] = {'bind': '/usr/src/app/input'}
    # execute actual tool image with provided settings
    try: 
        docker_client.containers.run(image,
                                volumes=_volumes,
                                network='host',
                                environment=env,
                                command=cmd,
                                auto_remove=True
                                )
    except errors.ImageNotFound:
        print(f"[Error] Container image {image} not found!")
        return {"error": f"container image {image} not found!"}
    print("Done")
    print("Correcting ownership of pipeline step output ...")
    chown_output(OUTPUT_UID, output_dir)
    return {"image_used": image, "output_dir": output_dir}

@routes.post('/run')
async def init(request):
    data = await request.json()
    image = data['image']
    input_dir = data['input_dir']
    output_dir = data['output_dir']
    env = data['env']
    cmd = data['cmd']
    docker_socket = data['docker_socket']
    response = pipeline_run(image, input_dir, output_dir, env, cmd, docker_socket)
    return web.json_response(response)

app.add_routes(routes)
if __name__ == '__main__':
    web.run_app(app, port=8081)
