from twisted.internet import protocol
from twisted.internet import reactor
from twisted.internet import task

class Echo(protocol.Protocol):
    def __init__(self):
        loopcall = task.LoopingCall(self.pollForData)
        loopcall.start(1).addErrback(self.errorOccured) # call every second

    def errorOccured(self):
        print("ERROR %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
        
    def pollForData(self):
        print("yo")
            
    def dataReceived(self, data):
        self.transport.write(data)

class EchoFactory(protocol.Factory):
    def buildProtocol(self, addr):
        return Echo()

reactor.listenTCP(8000, EchoFactory())
reactor.run()
