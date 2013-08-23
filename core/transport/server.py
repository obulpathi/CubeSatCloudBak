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
            self.sendChunk(packet)
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
    def transmitChunk(self, packet):
        self.transport.write(chunk)

# Server factory
class TransportServerFactory(protocol.Factory):
    def __init__(self):
        self.id = 0
        self.registrationCount = 0
        
    def buildProtocol(self, addr):
        return TransportServerProtocol(self)
