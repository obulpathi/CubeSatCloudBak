import pickle
from time import sleep

from twisted.python import log
from twisted.internet import reactor
from twisted.internet import protocol

from cloud.common import *

class TransportServerProtocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory
        
    # received data                        
    def dataReceived(self, packetstring):
        packet = pickle.loads(packetstring)
        if packet.flags == REGISTER:
            if packet.source == "GroundStation":
                self.registerGroundStation(packet)
            else:
                self.registerCubeSat(packet)
        elif packet.flags == UNREGISTER:
            self.unregister(packet)
        elif packet.flags == GET_MISSION:
            self.sendMission(packet.sender)
        elif packet.flags == CHUNK:
            self.receiveChunk(packet)
        else:
            log.msg("Unknown stuff >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>...")
            log.msg(packet)
    
    # register groundstation
    def registerGroundStation(self, packet):
        log.msg("registered ground station")
        self.factory.registrationCount = self.factory.registrationCount + 1
        packet = Packet(self.factory.address, "receiver", self.factory.address, self.factory.registrationCount, REGISTERED, \
                        self.factory.registrationCount, HEADERS_SIZE)
        packetstring = pickle.dumps(packet)
        self.transport.write(packetstring)
    
    # unregister what?
    def unregister(self, packet):
        log.msg("TODO: unregistered WHAT?? ^&%&^#%@&^#%@#&^ >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    
    # register CubeSat
    def registerCubeSat(self, packet):
        log.msg("registering CubeSat")
        new_packet = Packet(self.factory.address, packet.sender, self.factory.address, packet.source, REGISTERED, \
                        None, HEADERS_SIZE)
        packetstring = pickle.dumps(new_packet)
        self.transport.write(packetstring)

    # send mission to ground station
    def sendMission(self, receiver):
        log.msg("Sending mission >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>...")
        packet = Packet(self.factory.address, receiver, self.factory.address, "Master", MISSION, \
            TORRENT, HEADERS_SIZE)
        packetstring = pickle.dumps(packet)
        self.transport.write(packetstring)

# Server factory
class TransportServerFactory(protocol.Factory):
    def __init__(self):
        self.address = "Server"
        self.registrationCount = 100
        
    def buildProtocol(self, addr):
        return TransportServerProtocol(self)
