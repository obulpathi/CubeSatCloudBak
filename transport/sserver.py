from twisted.python import log
from twisted.internet import task
from twisted.internet import reactor
from twisted.internet import protocol
from twisted.protocols.basic import LineReceiver

from cloud.common import *

class TransportSServerProtocol(LineReceiver):
    def __init__(self, factory):
        self.factory = factory
        self.waiter = WaitForData(self.factory.fromServerToSServer, self.getData)
        self.waiter.start()

    def getData(self, line):
        log.msg("SServer: Got a packet, uplinking to Master Client")
        self.sendLine(line)
    
    def lineReceived(self, line):
        log.msg("SServer: Got a packet, sending Server")
        self.factory.fromSServerToServer.put(line)
        
    def connectionMade(self):
        log.msg("Connection made")

    def lineReceived(self, line):
        self.uplinkToCubeSat(line)


class TransportSServerFactory(protocol.Factory):
    def __init__(self, fromSServerToServer, fromServerToSServer):
        self.fromSServerToServer = fromSServerToServer
        self.fromServerToSServer = fromSServerToServer
        
    def buildProtocol(self, addr):
        return TransportGSServerProtocol(self)
