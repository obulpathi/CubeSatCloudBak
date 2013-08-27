import pickle
import threading

from twisted.python import log
from twisted.internet import task
from twisted.internet import reactor
from twisted.internet import protocol

from cloud.core.common import *
            
class TransportGSClientProtocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory
        self.id = None
        self.waiter = WaitForData(self.factory.fromGSServerToGSClient, self.getData)
        self.waiter.start()

    def getData(self, data):
        self.transport.write(data)
        
    def connectionMade(self):
        log.msg("GSClient connection made")
        self.register()
    
    def dataReceived(self, packetstring):
        packet = pickle.loads(packetstring)
        log.msg("data received")
        log.msg(packet)
        if self.id and packet.destination != self.id:
            log.msg("Destination: ", packet.destination)
            log.msg("uplinking data to cubesat")
            self.uplinkToCubeSat(packet)
        elif packet.flags & REGISTERED:
            self.registered(packet)
        elif packet.flags & CHUNK:
            self.receivedChunk(packet)
        else:
            log.msg("Server said: %s" % packetstring)
    
    def register(self):
        log.msg("registering")
        packet = Packet("GroundStation", MASTER_ID, "GroundStation", MASTER_ID, REGISTER, None, HEADERS_SIZE)
        data = pickle.dumps(packet)
        self.transport.write(data)
        
    def registered(self, packet):
        log.msg("Whoa!!!!!")
        self.id = packet.payload
        self.status = REGISTERED
        
    def deregister(self):
        log.msg("TODO: DEREGISTRAITON >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        self.transport.loseConnection()
    
    def downlinkFromCubeSat(self, packet):
        self.transport.write(packetstring)
    
    def uplinkToCubeSat(self, packet):
        log.msg("sending data througn pipes")
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
