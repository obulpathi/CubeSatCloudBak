import time
import pickle
import os.path

from twisted.internet import reactor, protocol
from twisted.protocols.basic import LineReceiver

class EchoClient(LineReceiver):
    def connectionMade(self):
        print("Connection made")
        self.setRawMode()
        data = ["a", "b", "c"]
        self.sendLine(pickle.dumps(data))
        #filename = "data.jpg"
        #self.setRawMode()
        #self.sendLine(open(filename, "r").read())
        #self.sendLine(data)

    def connectionLost(self, reason):
        print "connection lost"
        print(reason)

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
