import pickle

from twisted.python import log
from twisted.internet import task
from twisted.internet import reactor
from twisted.internet import protocol
from twisted.protocols.basic import LineReceiver

from cloud import utils
from cloud.common import *

class TransportCSServerProtocol(LineReceiver):
    def __init__(self, factory, fromWorkerToCSServer, fromCSServerToWorker):
        self.factory = factory
        self.fromWorkerToCSServer = fromWorkerToCSServer
        self.fromCSServerToWorker = fromCSServerToWorker
        self.waiter = WaitForData(self.fromWorkerToCSServer, self.getData)
        self.waiter.start()
        self.setLineMode()

    def getData(self, line):
        # print "Router got data from worker master", line
        self.sendLine(line)
    
    def lineReceived(self, line):
        # print "Router received line from worker client", line
        self.fromCSServerToWorker.put(line)
    
    def connectionMade(self):
        print "Connection made"
        # log.msg("Connection made")
    
    def replicateChunk(self):
        log.msg("replicate chunk")
    
class TransportCSServerFactory(protocol.Factory):
    def __init__(self, fromWorkerToCSServers, fromCSServersToWorker):
        self.fromWorkerToCSServers = fromWorkerToCSServers
        self.fromCSServersToWorker = fromCSServersToWorker
        self.count = 0
        
    def buildProtocol(self, addr):
        fromWorkerToCSServer = self.fromWorkerToCSServers[self.count]
        fromCSServerToWorker = self.fromCSServersToWorker[self.count]
        self.count = self.count + 1
        return TransportCSServerProtocol(self, fromWorkerToCSServer, fromCSServerToWorker)
        
    def clientConnectionFailed(self, connector, reason):
        log.msg(reason)
        reactor.stop()
