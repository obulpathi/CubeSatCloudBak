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
        log.msg("GSServer: Got a packet, uplinking to worker")
        self.transport.write(packetstring)
             
    def dataReceived(self, packetstring):
        log.msg("GSServer: Got a packet, sending GSClient")
        self.factory.fromGSServerToGSClient.put(packetstring)


class TransportGSServerFactory(protocol.Factory):
    def __init__(self, fromGSClientToGSServer, fromGSServerToGSClient):
        self.fromGSClientToGSServer = fromGSClientToGSServer
        self.fromGSServerToGSClient = fromGSServerToGSClient
        
    def buildProtocol(self, addr):
        return TransportGSServerProtocol(self)
