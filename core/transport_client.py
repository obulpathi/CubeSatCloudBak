import threading
from twisted.internet import reactor
from twisted.internet import protocol
from threading import Thread

class TransportClientProtocol(protocol.Protocol):
    def connectionMade(self):
        self.register()
        
    def dataReceived(self, data):
        if data == "REGISTERED":
            self.registered()
        elif data == "CHUNK":
            self.receivedChunk()
        else:
            print "Server said:", data
    
    def register(self):
        self.transport.write("REGISTER")
    
    def registered(self):
        pass
    
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

class TransportClient(threading.Thread):
    def __init__(self):
        reactor.connectTCP("localhost", 8000, TransportClientFactory())
        threading.Thread.__init__(self)
        
    def run(self):
        pass

if __name__ == "__main__":
    client = TransportClient()
    twistedThread = Thread(target=reactor.run, args = (False,));
    twistedThread.start()
