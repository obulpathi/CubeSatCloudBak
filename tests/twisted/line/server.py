import os
import sys
import math
import pickle

from twisted.internet import reactor, protocol
from twisted.protocols.basic import LineReceiver

MAX_PACKET_SIZE = 1000

class Echo(LineReceiver):
    def connectionMade(self):
        print("Connection made")
        self.setLineMode()
        self.sendData()

    def connectionLost(self, reason):
        print("Connection lost")
        print(reason)

    def lineReceived(self, data):
        print "line received"
    
    def sendMetadata(self):
        self.sendLine(metadata)

    def sendData(self):
        metadata = ""
        data = None
        chunks = os.listdir("image")
        for chunk in chunks:
            fragment = open("image/" + chunk).read()
            metadata = metadata + ":" + chunk + ":" + str(len(fragment))
            if data:
                data = data + fragment
            else:
                data = fragment
        metadata = str(len(data)) + metadata
        self.sendLine(metadata)
        self.setRawMode()
        length = len(data)
        for i in range(int(math.ceil(float(length)/MAX_PACKET_SIZE))):
            self.transport.write(data[i*MAX_PACKET_SIZE:(i+1)*MAX_PACKET_SIZE])
        
    def rawDataReceived(self, data):
        print("raw data received")

def main():
    """This runs the protocol on port 8000"""
    factory = protocol.ServerFactory()
    factory.protocol = Echo
    factory.clients = []
    reactor.listenTCP(4444,factory)
    reactor.run()

# this only runs if the module was *not* imported
if __name__ == '__main__':
    main()
