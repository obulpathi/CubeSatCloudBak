import pickle

from twisted.internet import task
from twisted.internet import reactor
from twisted.internet import protocol

from cloud.core.common import *

class TransportGSServerProtocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory

        loopcall = task.LoopingCall(self.pollForDataFromGSClient)
        loopcall.start(0.1) # call every second

    def pollForDataFromGSClient(self):
        try:
            packet = self.factory.fromGSClientToGSServer.get(False)
            if packet:
                print("GSServer received data from GSClient")
                print("uplinking data")
                print(packet)
                self.transport.write(pickle.dumps(packet))
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
        self.factory.fromGSServerToGSClient.put(packetstring)
        
    def transmitChunk(self):
        self.transport.write(chunk)
    
    def replicateChunk(self):
        print("replicate chunk")
    
class TransportGSServerFactory(protocol.Factory):
    def __init__(self, fromGSClientToGSServer, fromGSServerToGSClient):
        self.fromGSClientToGSServer = fromGSClientToGSServer
        self.fromGSServerToGSClient = fromGSServerToGSClient
    def buildProtocol(self, addr):
        return TransportGSServerProtocol(self)
