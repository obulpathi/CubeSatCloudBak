from cubesatclient import CubeSatClient
from cubesatserver import CubeSatServer

client = CubeSatClient()
server = CubeSatServer()
print "starting server"
server.start()
print "started server"
print "starting client"
client.start()
print "started client"
