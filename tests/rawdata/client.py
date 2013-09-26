import time
import pickle
import os.path

from twisted.internet import reactor, protocol
from twisted.protocols.basic import LineReceiver

class Client(LineReceiver):
    def connectionMade(self):
        print("Connection made")
        self.getChunk()

    def connectionLost(self, reason):
        print "connection lost"
        print(reason)

    def lineReceived(self, data):
        print "raw data"
        if self.status == "CHUNK":
            metadata = data
            print(metadata)
            self.setRawMode()
        else:
            "line received"

    def rawDataReceived(self, data):
        print "raw data"
        if self.status == "CHUNK":
            self.gotChunk(data)
        else:
            print("raw data received")

    def getChunk(self):
        print "get chunk"
        self.setLineMode()
        self.sendLine("CHUNK")
        self.status = "CHUNK"

    def gotChunk(self, data):
        print "got chunk"
        chunk = open("data.jpg", "w")
        chunk.write(data)
        chunk.close()
        self.setLineMode()

class ClientFactory(protocol.ClientFactory):
    protocol = Client

    def clientConnectionFailed(self, connector, reason):
        print "Connection failed - goodbye!"
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        print "Connection lost - goodbye!"
        reactor.stop()


# this connects the protocol to a server runing on port 8000
def main():
    f = ClientFactory()
    reactor.connectTCP("localhost", 4444, f)
    reactor.run()

# this only runs if the module was *not* imported
if __name__ == '__main__':
    main()
