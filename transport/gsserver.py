import pickle

from twisted.python import log
from twisted.internet import task
from twisted.internet import reactor
from twisted.internet import protocol

from cloud.core.common import *

class TransportGSServerProtocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory
        self.waiter = WaitForData(self.factory.fromGSClientToGSServer, self.getData)
        self.waiter.start()

    def getData(self, packet):
        log.msg("GSServer received data from GSClient")
        log.msg("uplinking data")
        log.msg(packet)
        self.transport.write(pickle.dumps(packet))
    
    def connectionMade(self):
        log.msg("router connection made")
             
    def dataReceived(self, packetstring):
        packet = pickle.loads(packetstring)
        if packet.flags & REGISTER:
            self.registerWorker(packetstring)
        elif packet.flags & GET_CHUNK:
            self.sendChunk(packet)
        else:
            log("Unknown stuff")
    
    def forwardToChild(self, packet):
        log.msg("data received from master")
        
    def registerWorker(self, packetstring):
        log.msg("router got the registration request")
        # send this packet to master
        self.factory.fromGSServerToGSClient.put(packetstring)
        
    def transmitChunk(self):
        self.transport.write(chunk)
    
    def replicateChunk(self):
        log.msg("replicate chunk")
    
class TransportGSServerFactory(protocol.Factory):
    def __init__(self, fromGSClientToGSServer, fromGSServerToGSClient):
        self.fromGSClientToGSServer = fromGSClientToGSServer
        self.fromGSServerToGSClient = fromGSServerToGSClient
    def buildProtocol(self, addr):
        return TransportGSServerProtocol(self)
