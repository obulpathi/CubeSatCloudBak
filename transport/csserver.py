import pickle

from twisted.internet import task
from twisted.internet import reactor
from twisted.internet import protocol

from cloud.common import *

class TransportCSServerProtocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory
        self.waiter = WaitForData(self.factory.fromWorkerToCSServer, self.getData)
        self.waiter.start()

    def getData(self, data):
        log.msg(data)
        self.transport.write(data)
        
    def connectionMade(self):
        log.msg("Connection made")
                
    def dataReceived(self, packetstring):
        self.fromCSServerToWorker.put(packetstring)
        
    def forwardToChild(self, packet):
        log.msg("data received from master")
        
    def registerWorker(self, packetstring):
        log.msg("router got the registration request")
        # send this packet to master
        self.factory.fromCSServerToWorker.put(packetstring)
    
    def replicateChunk(self):
        log.msg("replicate chunk")
    
class TransportCSServerFactory(protocol.Factory):
    def __init__(self, fromWorkerToCSServer, fromCSServerToWorker):
        self.fromWorkerToCSServer = fromWorkerToCSServer
        self.fromCSServerToWorker = fromCSServerToWorker
        
    def buildProtocol(self, addr):
        return TransportCSServerProtocol(self)
