import pickle

from twisted.python import log
from twisted.internet import task
from twisted.internet import reactor
from twisted.internet import protocol
from twisted.protocols.basic import LineReceiver

from cloud.common import *

class TransportCSServerProtocol(LineReceiver):
    def __init__(self, factory):
        self.factory = factory
        self.waiter = WaitForData(self.factory.fromWorkerToCSServer, self.getData)
        self.waiter.start()

    def getData(self, line):
        print "Router got data from worker master", line
        self.sendLine(line)
    
    def lineReceived(self, line):
        print "Router received line from worker client", line
        self.factory.fromCSServerToWorker.put(line)
    
    def connectionMade(self):
        print "### connection made"
        # log.msg("Connection made")
    
    def replicateChunk(self):
        log.msg("replicate chunk")
    
class TransportCSServerFactory(protocol.Factory):
    def __init__(self, fromWorkerToCSServer, fromCSServerToWorker):
        self.fromWorkerToCSServer = fromWorkerToCSServer
        self.fromCSServerToWorker = fromCSServerToWorker
        
    def buildProtocol(self, addr):
        return TransportCSServerProtocol(self)
        
    def clientConnectionFailed(self, connector, reason):
        log.msg("########### Connection failed.")
        print reason
        reactor.stop()
