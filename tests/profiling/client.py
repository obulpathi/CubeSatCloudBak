import time
import pickle
from twisted.internet import reactor, protocol

class EchoClient(protocol.Protocol):
    def __init__(self):
        self.fragments = None
        self.length = 0
        
    def connectionMade(self):
        self.t1 = time.time()
        self.transport.write("hello, world!")
    
    def dataReceived(self, fragment):
        if not self.fragments:
            self.length = int(fragment[:6])
            self.fragments = fragment[6:]
        else:
            self.fragments = self.fragments + fragment
            
        if self.length == len(self.fragments):
            self.chunkReceived(pickle.loads(self.fragments))
    
    def connectionLost(self, reason):
        print "connection lost"

    def chunkReceived(self, data):
        chunk = open("chunk.jpg", "w")
        chunk.write(data)
        chunk.close()
        self.t2 = time.time()
        print "Time: ", (self.t2 - self.t1)
        
class EchoFactory(protocol.ClientFactory):
    protocol = EchoClient

    def clientConnectionFailed(self, connector, reason):
        print "Connection failed - goodbye!"
        reactor.stop()
    
    def clientConnectionLost(self, connector, reason):
        print "Connection lost - goodbye!"
        reactor.stop()


# this connects the protocol to a server runing on port 8000
def main():
    f = EchoFactory()
    reactor.connectTCP("localhost", 8000, f)
    reactor.run()

# this only runs if the module was *not* imported
if __name__ == '__main__':
    main()
