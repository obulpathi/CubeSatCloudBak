import pickle

from twisted.internet import task
from twisted.internet import reactor
from twisted.internet import protocol

from cloud.common import *

class TransportCSServerProtocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory

        loopcall = task.LoopingCall(self.pollForDataFromCSClient)
        loopcall.start(0.1) # call every second

    def pollForDataFromCSClient(self):
        try:
            packet = self.factory.fromCSClientToCSServer.get(False)
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
            self.registerCSClient(packetstring)
        elif packet.flags & GET_CHUNK:
            self.sendChunk(packet)
        else:
            log("Unknown stuff")
    
    def forwardToChild(self, packet):
        log.msg("data received from master")
        
    def registerWorker(self, packetstring):
        log.msg("router got the registration request")
        # send this packet to master
        self.factory.fromCSServerToCSClient.put(packetstring)
        
    def transmitChunk(self):
        self.transport.write(chunk)
    
    def replicateChunk(self):
        log.msg("replicate chunk")
    
class TransportCSServerFactory(protocol.Factory):
    def __init__(self, fromCSClientToCSServer, fromCSServerToCSClient):
        self.fromCSClientToCSServer = fromCSClientToCSServer
        self.fromCSServerToCSClient = fromCSServerToCSClient
    def buildProtocol(self, addr):
        return TransportCSServerProtocol(self)
