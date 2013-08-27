import pickle

from twisted.internet import task
from twisted.internet import reactor
from twisted.internet import protocol

from cloud.core.common import *

class TransportRouterProtocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory

        loopcall = task.LoopingCall(self.pollForDataFromWorker)
        loopcall.start(0.1) # call every second

    def pollForDataFromWorker(self):
        try:
            packet = self.factory.fromWorkerToRouter.get(False)
            if not packet:
                return
            if packet.flags & REGISTERED:
                self.transport.write(pickle.dumps(packet))
            else:
                log.msg("received unknown packet type")
        except Exception:
            pass

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
        self.factory.fromRouterToWorker.put(packetstring)
        
    def transmitChunk(self):
        self.transport.write(chunk)
    
    def replicateChunk(self):
        log.msg("replicate chunk")
    
class TransportRouterFactory(protocol.Factory):
    def __init__(self, fromWorkerToRouter, fromRouterToWorker):
        self.fromWorkerToRouter = fromWorkerToRouter
        self.fromRouterToWorker = fromRouterToWorker
    def buildProtocol(self, addr):
        return TransportRouterProtocol(self)
