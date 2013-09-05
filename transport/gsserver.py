import pickle

from twisted.python import log
from twisted.internet import reactor
from twisted.internet import protocol

from cloud.common import *

class TransportGSServerProtocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory
        self.waiter = WaitForData(self.factory.fromGSClientToGSServer, self.getData)
        self.waiter.start()

    def getData(self, packetstring):
        self.transport.write(packetstring)
    
    def connectionMade(self):
        log.msg("Connection made between GSServer and CSClient")
             
    def dataReceived(self, packetstring):
        self.factory.fromGSServerToGSClient.put(packetstring)
        
    def forwardToChild(self, packet):
        log.msg("data received from master")
    
class TransportGSServerFactory(protocol.Factory):
    def __init__(self, fromGSClientToGSServer, fromGSServerToGSClient):
        self.fromGSClientToGSServer = fromGSClientToGSServer
        self.fromGSServerToGSClient = fromGSServerToGSClient
    def buildProtocol(self, addr):
        return TransportGSServerProtocol(self)
