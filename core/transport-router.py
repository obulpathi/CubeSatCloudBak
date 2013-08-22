import threading
from twisted.internet import reactor
from twisted.internet import protocol

class TransportRouterProtocol(protocol.Protocol):
    def connectionMade(self):
        global router
        router = self
        print("router connection made")
                
    def dataReceived(self, data):
        print("got data")
        if data == "REGISTER":
            print("registering slave")
            self.registerSlave();
        elif data == "GET_CHUNK":
            self.sendChunk()
        else:
            log("Unknown stuff")
    
    def registerSlave(self):
        self.transport.write("REGISTERED")
        
    def transmitChunk(self):
        self.transport.write(chunk)
    
    def replicateChunk(self):
        print("replicate chunk")
    
class TransportRouterFactory(protocol.Factory):
    def buildProtocol(self, addr):
        return TransportRouterProtocol()
