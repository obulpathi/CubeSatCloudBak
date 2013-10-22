from twisted.python import log
from twisted.internet import task
from twisted.internet import reactor
from twisted.internet import protocol
from twisted.protocols.basic import LineReceiver

from cloud import utils
from cloud.common import *

class TransportSServerProtocol(LineReceiver):
    def __init__(self, factory):
        self.factory = factory
        # self.MAX_LENGTH = 50000
        self.waiter = WaitForData(self.factory.fromServerToSServer, self.getData)
        self.waiter.start()
        self.setLineMode()

    def connectionMade(self):
        log.msg("SServer: connection made")
        
    def getData(self, line):
        self.sendLine(line)
        log.msg("SServer: Got a packet, uplinking to Master Client")
        log.msg(line)
    
    def lineReceived(self, line):
        log.msg("SServer: Got a packet, sending Server")
        log.msg(line)
        self.sendLine(line)
        #self.factory.fromSServerToServer.put(line)
        
    def connectionMade(self):
        log.msg("Connection made")


class TransportSServerFactory(protocol.Factory):
    def __init__(self, fromSServerToServer, fromServerToSServer):
        self.fromSServerToServer = fromSServerToServer
        self.fromServerToSServer = fromServerToSServer
        
    def buildProtocol(self, addr):
        return TransportSServerProtocol(self)
