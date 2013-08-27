import pickle

from twisted.python import log
from twisted.internet import task
from twisted.internet import reactor
from twisted.internet import protocol

from cloud.common import *

class TransportWorkerProtocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory
        self.id = None
        self.waiter = WaitForData(self.factory.fromCSServerToWorker, self.getData)
        self.waiter.start()

    def getData(self, data):
        log.msg(data)
        self.transport.write(data)

    def connectionMade(self):
        log.msg("Worker connection made")
        self.register()
    
    def dataReceived(self, packetstring):
        packet = pickle.loads(packetstring)
        log.msg("data received")
        # check if packet is for self
        if self.id and packet.destination != self.id:
            log.msg(packet.destination)
            log.msg(self.id)
            log.msg("forwarding data to child")
            self.forwardToChild(packet)
        elif packet.flags & REGISTERED:
            self.registered(packet)
        elif packet.flags & CHUNK:
            self.receivedChunk(packet)
        else:
            log.msg("Server said: %s" % packetstring)
    
    def register(self):
        log.msg("registering")
        packet = Packet("sender", "receiver", "worker", "destination", REGISTER, None, HEADERS_SIZE)
        data = pickle.dumps(packet)
        self.transport.write(data)
        
    def registered(self, packet):
        log.msg("Whoa!!!!!")
        self.id = packet.payload
        self.status = IDLE
        self.requestChunk()
        
    def deregister(self):
        self.transport.loseConnection()

    def forwardToServer(self, packet):
        self.factory.fromWorkerToCSClient.put(packet)
            
    def forwardToChild(self, packet):
        self.factory.fromWorkerToCSServer.put(packet)
        
    def requestChunk(self):
        log.msg("requesting chunk")
        packet = Packet(self.id, "receiver", self.id, "destination", GET_CHUNK, None, HEADERS_SIZE)
        data = pickle.dumps(packet)
        self.transport.write(data)
    
    def receivedChunk(self, packet):
        log.msg("Chunk received")
        chunk = open("chunk1.jpg", "wb")
        chunk.write(packet.payload.data)
        chunk.close()

            
class TransportWorkerFactory(protocol.ClientFactory):
    def __init__(self, fromWorkerToCSClient, fromCSClientToWorker):
        self.fromWorkerToCSClient = fromWorkerToCSClient
        self.fromCSClientToWorker = fromCSClientToWorker
    def buildProtocol(self, addr):
        return TransportWorkerProtocol(self)
    def clientConnectionFailed(self, connector, reason):
        log.msg("Connection failed.")
        reactor.stop()
    def clientConnectionLost(self, connector, reason):
        log.msg("Connection lost.")
        reactor.stop()
