import pickle
import threading

from twisted.python import log
from twisted.internet import task
from twisted.internet import reactor
from twisted.internet import protocol

from cloud.common import *
            
class TransportGSClientProtocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory
        self.address = "GroundStation"
        self.waiter = WaitForData(self.factory.fromGSServerToGSClient, self.getData)
        self.waiter.start()
        self.state = UNREGISTERED # whats the begin state?

    def getData(self, data):
        self.transport.write(data)
        
    def connectionMade(self):
        log.msg("Connection made")
        self.register()
    
    def dataReceived(self, packetstring):
        packet = pickle.loads(packetstring)
        log.msg(packet)
        if self.address == "GroundStation" and packet.flags & REGISTERED:
            self.registered(packet)
        elif packet.destination != self.address:
            self.uplinkToCubeSat(packetstring)
        else:
            log.msg("Server said: %s " % packetstring)
    
    def register(self):
        packet = Packet(self.address, "Server", self.address, "Server", REGISTER, None, HEADERS_SIZE)
        data = pickle.dumps(packet)
        self.transport.write(data)
        
    def registered(self, packet):
        self.address = packet.payload
        self.status = REGISTERED
        
    def deregister(self):
        log.msg("TODO: Deregistration")
        self.transport.loseConnection()
    
    def downlinkFromCubeSat(self, packet):
        self.transport.write(packetstring)
    
    def uplinkToCubeSat(self, packet):
        self.factory.fromGSClientToGSServer.put(packet)


class TransportGSClientFactory(protocol.ClientFactory):
    def __init__(self, fromGSClientToGSServer, fromGSServerToGSClient):
        self.fromGSClientToGSServer = fromGSClientToGSServer
        self.fromGSServerToGSClient = fromGSServerToGSClient
        
    def buildProtocol(self, addr):
        return TransportGSClientProtocol(self)
        
    def clientConnectionFailed(self, connector, reason):
        log.msg("Connection failed.")
        reactor.stop()
        
    def clientConnectionLost(self, connector, reason):
        log.msg("Connection lost.")
        reactor.stop()
