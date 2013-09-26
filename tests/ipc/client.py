from twisted.internet import task
from twisted.internet import reactor
from twisted.internet import protocol

class Client(protocol.Protocol):
    def connectionMade(self):
        self.transport.write("Hello, world!")
    def dataReceived(self, data):
        print "Server said:", data
        task.deferLater(reactor, 1, self.sendData)
    def sendData(self):
        self.transport.write("Hello, world!")


class ClientFactory(protocol.ClientFactory):
    def buildProtocol(self, addr):
        return Client()
    def clientConnectionFailed(self, connector, reason):
        print "Connection failed."
        reactor.stop()
    def clientConnectionLost(self, connector, reason):
        print "Connection lost."
        reactor.stop()


reactor.connectTCP("localhost", 8008, ClientFactory())
reactor.run()
