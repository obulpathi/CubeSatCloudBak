import sys
import pickle

from twisted.internet import reactor, protocol
from twisted.protocols.basic import LineReceiver

class Server(LineReceiver):
    def connectionMade(self):
        print("Connection made")
        self.setLineMode()

    def connectionLost(self, reason):
        print("Connection lost")
        print(reason)

    def lineReceived(self, data):
        print("line received")
        if data == "CHUNK":
            self.transmitChunk()
        else:
            print(data)

    def rawDataReceived(self, data):
        print("raw data received")

    def transmitChunk(self):
        print("transmitting chunk")
        chunk = open("chunk.jpg", "r")
        data = chunk.read()
        chunk.close()
        metadata = "data.jpg:one:two:1:2"
        self.sendLine(metadata)
        self.setRawMode()
        self.transport.write(data)
        self.setLineMode()

def main():
    """This runs the protocol on port 8000"""
    factory = protocol.ServerFactory()
    factory.protocol = Server
    factory.clients = []
    reactor.listenTCP(4444, factory)
    reactor.run()

# this only runs if the module was *not* imported
if __name__ == '__main__':
    main()
