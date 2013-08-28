import pickle

from twisted.python import log
from twisted.internet import task
from twisted.internet import reactor
from twisted.internet import protocol

from cloud.common import *

class TransportCSClientProtocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory
        self.id = None
        self.waiter = WaitForData(self.factory.fromWorkerToCSClient, self.getData)
        self.waiter.start()

    def getData(self, data):
        log.msg(data)
        self.transport.write(data)

    def connectionMade(self):
        log.msg("Worker connection made")
        self.status = REGISTERED
        # self.register()
    
    def dataReceived(self, packetstring):
        self.fromCSClientToWorker.put(packetstring)
    
    def register1(self):
        packet = Packet("sender", "receiver", "worker", "Server", REGISTER, None, HEADERS_SIZE)
        data = pickle.dumps(packet)
        self.transport.write(data)
        
    def registered1(self, packet):
        log.msg("Whoa!!!!!")
        self.id = packet.payload
        self.status = REGISTERED
        
    def deregister(self):
        self.transport.loseConnection()
        
            
class TransportCSClientFactory(protocol.ClientFactory):
    def __init__(self, fromWorkerToCSClient, fromCSClientToWorker):
        self.fromWorkerToCSClient = fromWorkerToCSClient
        self.fromCSClientToWorker = fromCSClientToWorker
    def buildProtocol(self, addr):
        return TransportCSClientProtocol(self)
    def clientConnectionFailed(self, connector, reason):
        log.msg("Connection failed.")
        reactor.stop()
    def clientConnectionLost(self, connector, reason):
        log.msg("Connection lost.")
        reactor.stop()
