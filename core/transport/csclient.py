import pickle

from twisted.python import log
from twisted.internet import task
from twisted.internet import reactor
from twisted.internet import protocol

from cloud.core.common import *

class TransportCSClientProtocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory
        self.waiter = WaitForData(self.factory.fromWorkerToCSClient, self.getData)
        self.waiter.start()

    def getData(self, data):
        log.msg(data)
        self.transport.write(data)

    def connectionMade(self):
        log.msg("CSClient -> GSServer Connection made")
        self.register()
    
    def dataReceived(self, packetstring):
        packet = pickle.loads(packetstring)
        log.msg("data received")
        if packet.flags == REGISTERED:
            self.registered(packet)
        else:
            log.msg("sending data to worker")
            log.msg(packet)
            self.factory.fromCSClientToWorker.put(packet)
    
    def register(self):
        log.msg("registering with ground station and server")
        packet = Packet(self.factory.address, "ground station", self.factory.address, SERVER_ID, REGISTER, None, HEADERS_SIZE)
        data = pickle.dumps(packet)
        self.transport.write(data)
        
    def registered(self, packet):
        log.msg("Whoa!!!!! >>> CubeSatClient Registered with Server #################")
        self.status = REGISTERED
        self.getCommand()
        
    def deregister(self):
        log.msg("TODO: DEREGISTRAITON >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        self.transport.loseConnection()
    
    def getCommand(self):
        log.msg("requesting server for command")
        packet = Packet(self.factory.address, "ground station", self.factory.address, SERVER_ID, COMMAND, None, HEADERS_SIZE)
        data = pickle.dumps(packet)
        self.transport.write(data)
            
    def downlinkToGroundStation(self, packet):
        self.transport.write(packetstring)
    
    def uplinkFromGroundStation(self, packet):
        pass


class TransportCSClientFactory(protocol.ClientFactory):
    def __init__(self, address, fromWorkerToCSClient, fromCSClientToWorker):
        self.address = address
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
