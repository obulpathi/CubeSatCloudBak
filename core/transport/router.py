import pickle

from twisted.internet import task
from twisted.internet import reactor
from twisted.internet import protocol

from cloud.core.common import *

class TransportRouterProtocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory

        loopcall = task.LoopingCall(self.pollForDataFromClient)
        loopcall.start(0.1) # call every second

    def pollForDataFromClient(self):
        try:
            packet = self.factory.fromClientToRouter.get(False)
            if not packet:
                return
            if packet.flags & REGISTERED:
                self.transport.write(pickle.dumps(packet))
            else:
                print("received unknown packet type")
        except Exception:
            pass

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
        self.factory.fromRouterToClient.put(packetstring)
        
    def transmitChunk(self):
        self.transport.write(chunk)
    
    def replicateChunk(self):
        print("replicate chunk")
    
class TransportRouterFactory(protocol.Factory):
    def __init__(self, fromClientToRouter, fromRouterToClient):
        self.fromClientToRouter = fromClientToRouter
        self.fromRouterToClient = fromRouterToClient
    def buildProtocol(self, addr):
        return TransportRouterProtocol(self)
