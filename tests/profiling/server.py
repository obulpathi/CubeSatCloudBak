import pickle
from twisted.internet import reactor, protocol

class Echo(protocol.Protocol):
    def dataReceived(self, data):
        self.sendChunk()
        
    def sendChunk(self):
        chunk = open("data.jpg", "r")
        data = chunk.read()
        chunk.close()
        picklestring = pickle.dumps(data)
        length = len(picklestring)
        data = str(length).zfill(6) + picklestring
        self.transport.write(data)
        
def main():
    """This runs the protocol on port 8000"""
    factory = protocol.ServerFactory()
    factory.protocol = Echo
    reactor.listenTCP(8000,factory)
    reactor.run()

# this only runs if the module was *not* imported
if __name__ == '__main__':
    main()
