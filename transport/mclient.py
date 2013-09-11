import pickle

from twisted.python import log
from twisted.internet import task
from twisted.internet import reactor
from twisted.internet import protocol

from cloud.common import *

class TransportMasterClientProtocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory
        self.address = None
        self.waiter = WaitForData(self.factory.fromMasterToMasterClient, self.getData)
        self.waiter.start()

    def getData(self, packet):
        log.msg(packet)
        self.transport.write(pickle.dumps(packet))

    def connectionMade(self):
        task.deferLater(reactor, 2, self.register)
    
    def dataReceived(self, packetstring):
        packet = pickle.loads(packetstring)
        log.msg(packet)
        self.factory.fromMasterClientToMaster.put(packet)
    
    def register(self):
        packet = Packet("MasterClient", "Master", "MasterClient", "Master", REGISTER, None, HEADERS_SIZE)
        self.factory.fromMasterClientToMaster.put(packet)
        
    def registered(self, packet):
        log.msg("Whoa!!!!!")
        self.address = packet.payload
        self.status = REGISTERED
        
    def deregister(self):
        self.transport.loseConnection()
        
            
class TransportMasterClientFactory(protocol.ClientFactory):
    def __init__(self, fromMasterToMasterClient, fromMasterClientToMaster):
        self.fromMasterToMasterClient = fromMasterToMasterClient
        self.fromMasterClientToMaster = fromMasterClientToMaster
        
    def buildProtocol(self, addr):
        return TransportMasterClientProtocol(self)
        
    def clientConnectionFailed(self, connector, reason):
        log.msg("Connection failed.")
        reactor.stop()
        
    def clientConnectionLost(self, connector, reason):
        log.msg("Connection lost.")
        reactor.stop()
