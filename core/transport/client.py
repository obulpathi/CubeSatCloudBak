import pickle

from twisted.internet import task
from twisted.internet import reactor
from twisted.internet import protocol

from cloud.core.common import *

class TransportClientProtocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory
        self.id = None
        loopcall = task.LoopingCall(self.pollForDataFromRouter)
        loopcall.start(0.1) # call every second

    def pollForDataFromRouter(self):
        try:
            data = self.factory.fromRouterToClient.get(False)
            if data:
                self.transport.write(data)
        except Exception:
            pass

    def connectionMade(self):
        print("client connection made")
        self.register()
    
    def dataReceived(self, packetstring):
        packet = pickle.loads(packetstring)
        print("data received")
        if self.id and packet.destination != self.id:
            self.forwardToChild(packet)
        elif packet.flags & REGISTERED:
            self.registered(packet)
        elif packet.flags & CHUNK:
            self.receivedChunk()
        else:
            print "Server said:", packetstring
    
    def register(self):
        print("registering")
        packet = Packet("sender", "receiver", "worker", "destination", REGISTER, None, HEADERS_SIZE)
        data = pickle.dumps(packet)
        self.transport.write(data)
        
    def registered(self, packet):
        print("Whoa!!!!!")
        self.id = packet.payload
        self.status = IDLE
        
    def deregister(self):
        self.transport.loseConnection()
    
    def forwardToMaster(self, packet):
        self.transport.write(packetstring)
    
    def forwardToChild(self, packet):
        self.factory.fromClientToRouter.put(packet)
        
    def requestChunk(self):
        self.transport.write("GET_CHUNK")
    
    def receiveChunk(self):
        pass
            
class TransportClientFactory(protocol.ClientFactory):
    def __init__(self, fromClientToRouter, fromRouterToClient):
        self.fromClientToRouter = fromClientToRouter
        self.fromRouterToClient = fromRouterToClient
    def buildProtocol(self, addr):
        return TransportClientProtocol(self)
    def clientConnectionFailed(self, connector, reason):
        print "Connection failed."
        reactor.stop()
    def clientConnectionLost(self, connector, reason):
        print "Connection lost."
        reactor.stop()
