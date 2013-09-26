from twisted.internet import protocol
from twisted.internet import reactor
from twisted.internet import task

import time

server = None
client = None

class RouterServer(protocol.Protocol):
    def dataReceived(self, data):
        global client
        if client:
            client.transport.write(data)

class RouterServerFactory(protocol.Factory):
    def buildProtocol(self, addr):
        global server
        server = RouterServer()
        return server

class RouterClient(protocol.Protocol):
    def dataReceived(self, data):
        global server
        if server:
            server.transport.write(data)

class RouterClientFactory(protocol.ClientFactory):
    def buildProtocol(self, addr):
        global client
        client = RouterClient()
        return client

reactor.connectTCP("localhost", 8000, RouterClientFactory())
reactor.listenTCP(8008, RouterServerFactory())
reactor.run()
