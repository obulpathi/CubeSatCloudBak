import pickle
import threading
from threading import Thread
from twisted.internet import reactor
from twisted.internet import protocol

from cloud.core.common import *

class TransportClientProtocol(protocol.Protocol):
    def connectionMade(self):
        global client
        client = self
        print("client connection made")
    
    def dataReceived(self, packet):
        if data == "REGISTERED":
            self.registered()
        elif data == "CHUNK":
            self.receivedChunk()
        else:
            print "Server said:", data
    
    def register(self):
        print("registering")
        packet = Packet("sender", "receiver", "source", "destination", REGISTER, None, HEADERS_SIZE)
        packetstring = pickle.dumps(packet)
        self.transport.write(packetstring)
    
    def registered(self):
        self.status = IDLE
        
    def deregister(self):
        self.transport.loseConnection()
        
    def requestChunk(self):
        self.transport.write("GET_CHUNK")
    
    def receiveChunk(self):
        pass
            
class TransportClientFactory(protocol.ClientFactory):
    def buildProtocol(self, addr):
        return TransportClientProtocol()
    def clientConnectionFailed(self, connector, reason):
        print "Connection failed."
        reactor.stop()
    def clientConnectionLost(self, connector, reason):
        print "Connection lost."
        reactor.stop()
