import time
import pickle
import os.path

from twisted.internet import reactor, protocol
from twisted.protocols.basic import LineReceiver

class EchoClient(LineReceiver):
    def connectionMade(self):
        self.bits = None
        print("Connection made")
        self.setLineMode()

    def connectionLost(self, reason):
        print "connection lost"
        print(reason)

    def lineReceived(self, metadata):
        print "line received", metadata
        self.setRawMode()
        self.receivedMetadata(metadata)
    
    def receivedMetadata(self, metadata):
        self.metadata = metadata
        self.chunks = []
        fields = metadata.split(":")
        self.totalLength = int(fields.pop(0))
        while fields:
            self.chunks.append([fields[0], int(fields[1])])
            fields = fields[2:]
        
    def rawDataReceived(self, data):
        if self.bits:
            self.bits = self.bits + data
        else:
            self.bits = data
        self.packetReceived()
        
    def packetReceived(self):
        while self.chunks and (len(self.bits) >= self.chunks[0][1]):
            length = self.chunks[0][1]
            name = self.chunks[0][0]
            data = self.bits[:length]
            self.bits = self.bits[length:]
            chunk = open("client/" + name, "w")
            chunk.write(data)
            chunk.close()
            self.chunks.pop(0)
        if not self.chunks:
            print "YAHOOOOOOOOOOOOOOOOOOOOOOOOOO!"
        else:
            print self.chunks
            
        
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
    reactor.connectTCP("localhost", 4444, f)
    reactor.run()

# this only runs if the module was *not* imported
if __name__ == '__main__':
    main()
