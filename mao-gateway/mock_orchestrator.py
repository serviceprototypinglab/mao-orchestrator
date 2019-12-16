from aiohttp import web
import subprocess
import configparser


app = web.Application()
routes = web.RouteTableDef()
config = configparser.ConfigParser()
config.read('mock.ini')
etcd_host = config['ETCD']['HOST']
etcd_port = int(config['ETCD']['PORT'])


@routes.post('/regnode')
async def register(request):
    data = await request.json()
    username = data['username']
    ip = data['ip']
    location = data['location']
    print(username)
    print(ip)
    response = subprocess.run("etcdctl --endpoints http://{}:{} member add {} http://{}:2380".format(etcd_host, etcd_port, username, ip),
                              shell=True,
                              stdout=subprocess.PIPE)
    return web.json_response(response.stdout.decode('utf-8'))



app.add_routes(routes)
if __name__ == '__main__':
    web.run_app(app)
