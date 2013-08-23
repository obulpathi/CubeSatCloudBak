import pickle

from twisted.internet import reactor
from twisted.internet import protocol

from cloud.core.common import *

class TransportServerProtocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory
        
    # received data                        
    def dataReceived(self, packetstring):
        packet = pickle.loads(packetstring)
        if packet.flags & REGISTER:
            self.registerSlave(packet)
        elif packet.flags & GET_CHUNK:
            self.transmitChunk(packet.source)
        else:
            log("Unknown stuff")
    
    # register slave
    def registerSlave(self, packet):
        print("registered slave")
        self.factory.registrationCount = self.factory.registrationCount + 1
        packet = Packet(self.factory.id, "receiver", self.factory.id, self.factory.registrationCount, REGISTERED, \
                        self.factory.registrationCount, HEADERS_SIZE)
        packetstring = pickle.dumps(packet)
        self.transport.write(packetstring)
    
    # transmit chunk
    def transmitChunk(self, destination):
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
        self.id = 0
        self.registrationCount = 0
        
    def buildProtocol(self, addr):
        return TransportServerProtocol(self)
