#!/usr/bin/env python

from twisted.internet import reactor, protocol

class QuickDisconnectProtocol(protocol.Protocol):
    def connectionMade(self):
        print "Connected to %s." % self.transport.getPeer().host
        self.transport.loseConnection()

class BasicClientFactory(protocol.ClientFactory):
    protocol = QuickDisconnectProtocol

    def clientConnectionLost(self, connector, reason):
        print "Lost connection: %s" % reason.getErrorMessage()
        reactor.stop()

    def clientConnectionFailed(self, connector, reason):
        print "Connection failed: %s" % reason.getErrorMessage()
        reactor.stop()

reactor.connectTCP('localhost', 80, BasicClientFactory())
reactor.run()
