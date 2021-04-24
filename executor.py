from aiohttp import web
import json
import docker
import json


app = web.Application()
routes = web.RouteTableDef()

docker_client = docker.from_env()

def pipeline_run(image, data_dir, env):
    print(f"Running image {image} with dir {data_dir}")
    docker_client.containers.run(image,
                             volumes={data_dir: {'bind': '/usr/src/app/data'}},
                             network='host',
                             environment=env,
                             auto_remove=True)
    print("Done")
    return {"image_used": image, "data_dir": data_dir}

@routes.post('/run')
async def init(request):
    data = await request.json()
    image = data['image']
    data_dir = data['data_dir']
    env = data['env']
    response = pipeline_run(image, data_dir, env)
    return web.json_response(response)

app.add_routes(routes)
if __name__ == '__main__':
    web.run_app(app, port=8081)
