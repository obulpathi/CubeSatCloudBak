import pickle

from twisted.python import log
from twisted.internet import reactor
from twisted.internet import protocol
from twisted.protocols.basic import LineReceiver

from cloud.common import *

class TransportGSServerProtocol(LineReceiver):
    def __init__(self, factory):
        self.factory = factory
        self.waiter = WaitForData(self.factory.fromGSClientToGSServer, self.getData)
        self.waiter.start()

    def getData(self, line):
        log.msg("GSServer: Got a packet, uplinking to worker")
        self.sendLine(line)
    
    def lineReceived(self, line):
        log.msg("GSServer: Got a packet, sending GSClient")
        self.factory.fromGSServerToGSClient.put(line)


class TransportGSServerFactory(protocol.Factory):
    def __init__(self, fromGSClientToGSServer, fromGSServerToGSClient):
        self.fromGSClientToGSServer = fromGSClientToGSServer
        self.fromGSServerToGSClient = fromGSServerToGSClient
        
    def buildProtocol(self, addr):
        return TransportGSServerProtocol(self)
