import logging
from twisted.internet import protocol, reactor

from cloud.core.common import *

class CubeSatServerProtocol(protocol.Protocol):
    def dataReceived(self, data):
        self.transport.write(data)
        
class CubeSatServerFactory(protocol.Factory):
    def buildProtocol(self, addr):
        return CubeSatServerProtocol()

class CubeSatClient(protocol.Protocol):
    def connectionMade(self):
        self.transport.write("Hello, world!")
    def dataReceived(self, data):
        print "Server said:", data
        self.transport.loseConnection()
        
class CubeSatClientFactory(protocol.ClientFactory):
    def buildProtocol(self, addr):
        return CubeSatClient()
    def clientConnectionFailed(self, connector, reason):
        print "Connection failed."
        reactor.stop()
    def clientConnectionLost(self, connector, reason):
        print "Connection lost."
        reactor.stop()

class Transceiver(object):
    def __init__(self):
        pass
        
    def send(self):
        reactor.connectTCP("localhost", 8000, CubeSatClientFactory())
        reactor.run()
    
    def receive(self):
        reactor.listenTCP(8000, CubeSatServerFactory())
        reactor.run()
