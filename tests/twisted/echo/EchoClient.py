from twisted.internet import reactor
from twisted.internet import protocol

from time import sleep

class EchoClient(protocol.Protocol):
    def connectionMade(self):
        self.transport.write("Hello, world!")
    def dataReceived(self, data):
        print "Server said:", data
        sleep(1)
        self.transport.write("Hello, world!")

class EchoFactory(protocol.ClientFactory):
    def buildProtocol(self, addr):
        return EchoClient()
    def clientConnectionFailed(self, connector, reason):
        print "Connection failed."
        reactor.stop()
    def clientConnectionLost(self, connector, reason):
        print "Connection lost."
        reactor.stop()
        
reactor.connectTCP("localhost", 8000, EchoFactory())
reactor.run()
