import pickle

from twisted.internet import task
from twisted.internet import reactor
from twisted.internet import protocol

from cloud.core.common import *

class TransportWorkerProtocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory
        self.id = None
        loopcall = task.LoopingCall(self.pollForDataFromRouter)
        loopcall.start(0.1) # call every second

    def pollForDataFromRouter(self):
        try:
            data = self.factory.fromRouterToWorker.get(False)
            if data:
                self.transport.write(data)
        except Exception:
            pass

    def connectionMade(self):
        print("Worker connection made")
        self.register()
    
    def dataReceived(self, packetstring):
        packet = pickle.loads(packetstring)
        print("data received")
        if self.id and packet.destination != self.id:
            print(packet.destination)
            print(self.id)
            print("forwarding data to child")
            self.forwardToChild(packet)
        elif packet.flags & REGISTERED:
            self.registered(packet)
        elif packet.flags & CHUNK:
            self.receivedChunk(packet)
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
        self.requestChunk()
        
    def deregister(self):
        self.transport.loseConnection()
    
    def forwardToMaster(self, packet):
        self.transport.write(packetstring)
    
    def forwardToChild(self, packet):
        self.factory.fromWorkerToRouter.put(packet)
        
    def requestChunk(self):
        print("requesting chunk")
        packet = Packet(self.id, "receiver", self.id, "destination", GET_CHUNK, None, HEADERS_SIZE)
        data = pickle.dumps(packet)
        self.transport.write(data)
    
    def receivedChunk(self, packet):
        print("Chunk received")
        chunk = open("chunk1.jpg", "wb")
        chunk.write(packet.payload.data)
        chunk.close()

            
class TransportWorkerFactory(protocol.ClientFactory):
    def __init__(self, fromWorkerToRouter, fromRouterToWorker):
        self.fromWorkerToRouter = fromWorkerToRouter
        self.fromRouterToWorker = fromRouterToWorker
    def buildProtocol(self, addr):
        return TransportWorkerProtocol(self)
    def clientConnectionFailed(self, connector, reason):
        print "Connection failed."
        reactor.stop()
    def clientConnectionLost(self, connector, reason):
        print "Connection lost."
        reactor.stop()
