from twisted.application import service, internet
from twisted.internet import protocol, reactor
from twisted.protocols import basic
import os

class FileDumpProtocol(basic.LineReceiver):
    def lineReceived(self, line):
        if hasattr(self, 'handle_' + line):
            getattr(self, 'handle_' + line)()
        else:
            self.listDir(line)

    def listDir(self, filename):
        try:
            f = open(filename)
            for line in f:
                self.transport.write(line)
        except Exception, e:
            self.sendLine("ERROR: %s" % e)

    def handle_quit(self):
        self.transport.loseConnection()

class FileDumpFactory(protocol.ServerFactory):
    protocol = FileDumpProtocol

UID = 1000
GID = 1000

fileDumpService = internet.TCPServer(23, FileDumpFactory())
application = service.Application("Cat Server", uid=UID, gid=GID)
fileDumpService.setServiceParent(application)
