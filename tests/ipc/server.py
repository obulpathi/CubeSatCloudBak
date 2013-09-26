from twisted.internet import protocol
from twisted.internet import reactor

class Server(protocol.Protocol):
    def __init__(self):
		pass

    def dataReceived(self, data):
        self.transport.write(data)

class ServerFactory(protocol.Factory):
    def buildProtocol(self, addr):
        return Server()

reactor.listenTCP(8000, ServerFactory())
reactor.run()
