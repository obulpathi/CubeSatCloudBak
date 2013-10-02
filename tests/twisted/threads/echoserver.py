from threading import Thread
from twisted.internet import reactor
from twisted.internet import protocol

class ServerProtocol(protocol.Protocol):
    def dataReceived(self, data):
        self.transport.write(data)
        
class ServerProtocolFactory(protocol.Factory):
    def buildProtocol(self, addr):
        return ServerProtocol()

class Server(Thread):
    def __init__(self):
        reactor.listenTCP(8000, ServerProtocolFactory())
        Thread.__init__(self)
        
    def run(self):
        reactor.run()

if __name__ == "__main__":    
    import time
    server = Server()
    Thread(target=reactor.run, args=(False,)).start()
    print "started server"
    for i in range(10):
        print i
        time.sleep(1)
