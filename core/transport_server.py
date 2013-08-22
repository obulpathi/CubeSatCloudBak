import threading
from twisted.internet import reactor
from twisted.internet import protocol

class TransportServerProtocol(protocol.Protocol):
    def dataReceived(self, data):
        if data == "REGISTER":
            self.registerSlave();
        elif data == "GET_CHUNK":
            self.sendChunk()
        else:
            log("Unknown stuff")
    
    def registerSlave(self):
        self.transport.write("REGISTERED")
        
    def transmitChunk(self):
        self.transport.write(chunk)
    
class TransportServerFactory(protocol.Factory):
    def buildProtocol(self, addr):
        return TransportServerProtocol()

class TransportServer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        
    def run(self):
        reactor.listenTCP(8000, TransportServerFactory())

    def transmit(self, data):
        pass
        
if __name__ == "__main__":
    transport_server = TransportServer()
    twistedThread = Thread(target=reactor.run, args = (False,));
