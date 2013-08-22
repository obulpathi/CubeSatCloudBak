import pickle
import threading
from twisted.internet import reactor
from twisted.internet import protocol

from cloud.core.common import *

class TransportServerProtocol(protocol.Protocol):
    def dataReceived(self, packetstring):
        print("got data %s" % packetstring)
        packet = pickle.loads(packetstring)
        if packet.flags & REGISTER:
            self.registerSlave(packet)
        elif packet.flags & GET_CHUNK:
            self.sendChunk(packet)
        else:
            log("Unknown stuff")
    
    def registerSlave(self, packet):
        print("registering slave")
        self.transport.write("REGISTERED")
        
    def transmitChunk(self, packet):
        self.transport.write(chunk)
    
class TransportServerFactory(protocol.Factory):
    def buildProtocol(self, addr):
        return TransportServerProtocol()
