from twisted.internet import protocol
from twisted.internet import reactor
from twisted.internet import task
from twisted.protocols.basic import LineReceiver
from twisted.internet.protocol import ServerFactory

class Echo(LineReceiver):
    def __init__(self):
        self.count = 0
            
    def dataReceived(self, data):
        print("Server count: %d\t%s" % (self.count, data))
        self.count = self.count + 1
        
class EchoFactory(ServerFactory):
    def buildProtocol(self, addr):
        return Echo()

reactor.listenTCP(8000, EchoFactory())
reactor.run()
