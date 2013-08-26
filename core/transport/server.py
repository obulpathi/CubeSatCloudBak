import pickle
from time import sleep

from twisted.internet import reactor
from twisted.internet import protocol

from cloud.core.common import *

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
            self.unregisterGroundStation(packet)
        elif packet.flags == COMMAND:
            self.sendCommand(packet)
        elif packet.flags == CHUNK:
            self.receiveChunk(packet)
        else:
            print("Unknown stuff")
    
    # register groundstation
    def registerGroundStation(self, packet):
        print("registered ground station")
        self.factory.registrationCount = self.factory.registrationCount + 1
        packet = Packet(self.factory.id, "receiver", self.factory.id, self.factory.registrationCount, REGISTERED, \
                        self.factory.registrationCount, HEADERS_SIZE)
        packetstring = pickle.dumps(packet)
        self.transport.write(packetstring)
    
    # unregister groundstation
    def unregisterGroundStaiton(self, packet):
        print("TODO: unregistered ground station ^&%&^#%@&^#%@#&^ >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    
    # register CubeSat
    def registerCubeSat(self, packet):
        print("registering CubeSat")
        new_packet = Packet(self.factory.id, packet.sender, self.factory.id, packet.source, REGISTERED, \
                        None, HEADERS_SIZE)
        packetstring = pickle.dumps(new_packet)
        self.transport.write(packetstring)
    
    # uplink mission command to CubeSat
    def sendCommand(self, packet):
        print("Uplinking the command")
        packet = Packet(1000, packet.sender, self.factory.id, MASTER_ID, TORRENT, \
            None, HEADERS_SIZE)
        packetstring = pickle.dumps(packet)
        self.transport.write(packetstring)
        
    # transmit command
    def transmitCommand(self, destination):
        print("Master got request for chunk")
        image = open("chunk.jpg", "rb")
        data = image.read()
        chunk = Chunk("chunkid", "size", "box", data)
        packet = Packet(self.factory.id, "receiver", self.factory.id, destination, CHUNK, \
                        chunk, HEADERS_SIZE)
        packetstring = pickle.dumps(packet)
        self.transport.write(packetstring)

# Server factory
class TransportServerFactory(protocol.Factory):
    def __init__(self):
        self.id = 100
        self.registrationCount = 100
        
    def buildProtocol(self, addr):
        return TransportServerProtocol(self)
