from twisted.internet import reactor
from twisted.internet import protocol

# Worker class
class Worker(object):
    # save the chunk
    def saveChunk(self, chunk):
        pass
    
    # process the chunk
    def cmap(self, chunkid):
        pass
    
    # downlink the chunk
    def downlink(self, chunkid):
        pass

class TransportClientProtocol(protocol.Protocol):
    def connectionMade(self):
        global client
        client = self
        print("client connection made")
    def dataReceived(self, data):
        print(data)
        
class TransportClientFactory(protocol.ClientFactory):
    def buildProtocol(self, addr):
        return TransportClientProtocol()
    def clientConnectionFailed(self, connector, reason):
        print "Connection failed."
        reactor.stop()
    def clientConnectionLost(self, connector, reason):
        print "Connection lost."
        reactor.stop()

class TransportRouterProtocol(protocol.Protocol):
    def connectionMade(self):
        global router
        router = self
        print("router connection made")
    def dataReceived(self, data):
        print(data)
    
class TransportRouterFactory(protocol.Factory):
    def buildProtocol(self, addr):
        return TransportRouterProtocol()
        
# run the worker and twisted reactor
if __name__ == "__main__":
    # start client
    reactor.connectTCP("localhost", 8008, TransportClientFactory())
    # start router
    reactor.listenTCP(8016, TransportRouterFactory())
    print("Client and Router are up and running")
    reactor.run()
