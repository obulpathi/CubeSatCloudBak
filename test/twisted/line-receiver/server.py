import sys
import pickle

from twisted.internet import reactor, protocol
from twisted.protocols.basic import LineReceiver

class Echo(LineReceiver):
    def connectionMade(self):
        print("Connection made")
        self.setRawMode()
        #self.setLineMode()

    def connectionLost(self, reason):
        print("Connection lost")
        print(reason)

    def lineReceived(self, data):
        print "line received"
        #print(data)
        """
        chunk = open("chunk.jpg", "w")
        chunk.write(data)
        chunk.close()
        """
    def rawDataReceived(self, data):
        print("raw data received")
        #print(data)
        """
        try:
            obj = pickle.loads(data)
            print obj
        except:
            print data
        """
        #self.transport.write("wa2")

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
