from threading import Thread
from twisted.internet import reactor
from twisted.internet import protocol

class ClientProtocol(protocol.Protocol):
    def connectionMade(self):
        self.transport.write("Hello, world!")
    def dataReceived(self, data):
        print "Server said:", data
        self.transport.loseConnection()
        
class ClientProtocolFactory(protocol.ClientFactory):
    def buildProtocol(self, addr):
        return ClientProtocol()
    def clientConnectionFailed(self, connector, reason):
        print "Connection failed."
        reactor.stop()
    def clientConnectionLost(self, connector, reason):
        print "Connection lost."
        reactor.stop()

class Client(Thread):
    def __init__(self):
        reactor.connectTCP("localhost", 8000, ClientProtocolFactory())
        Thread.__init__(self)
        
    def run(self):
        reactor.run()

if __name__ == "__main__":
    import time
    client = Client()
    Thread(target=reactor.run, args=(False,)).start()
    print "starting client"
    #client.start()
    print "started client"
