import pickle

from twisted.internet import reactor
from twisted.internet import protocol

from cloud.core.common import *

class TransportRouterProtocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory
        
    def connectionMade(self):
        print("router connection made")
                
    def dataReceived(self, packetstring):
        packet = pickle.loads(packetstring)
        if packet.flags & REGISTER:
            self.registerWorker(packetstring)
        elif packet.flags & GET_CHUNK:
            self.sendChunk(packet)
        else:
            log("Unknown stuff")
    
    def forwardToChild(self, packet):
        print("data received from master")
        
    def registerWorker(self, packetstring):
        print("router got the registration request")
        # send this packet to master
        self.factory.toClient.put(packetstring)
        
    def transmitChunk(self):
        self.transport.write(chunk)
    
    def replicateChunk(self):
        print("replicate chunk")
    
class TransportRouterFactory(protocol.Factory):
    def __init__(self, toClient):
        self.toClient = toClient
    def buildProtocol(self, addr):
        return TransportRouterProtocol(self)
