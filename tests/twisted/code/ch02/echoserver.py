from twisted.internet import reactor, protocol
from twisted.protocols import basic

class EchoProtocol(basic.LineReceiver):

    def connectionMade(self):
        print "Connection from", self.transport.getPeer().host
    
    def lineReceived(self, line):
        if line == 'quit':
            self.sendLine("Goodbye.")
            self.transport.loseConnection()
        else:
            self.sendLine("You said: " + line)

class EchoServerFactory(protocol.ServerFactory):
    protocol  = EchoProtocol

if __name__ == "__main__":
    port = 5001
    reactor.listenTCP(port, EchoServerFactory())
    print "Server running, press ctrl-C to stop."
    reactor.run()
