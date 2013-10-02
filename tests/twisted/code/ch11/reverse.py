from twisted.application import internet
from twisted.internet import protocol, reactor
from twisted.protocols import basic

def reverse(string):
    return string[::-1]

class ReverserProtocol(basic.LineReceiver):
    def lineReceived(self, line):
        if hasattr(self, 'handle_' + line):
            getattr(self, 'handle_' + line)()
        else:
            self.sendLine(reverse(line))

    def handle_quit(self):
        self.transport.loseConnection()

class ReverserFactory(protocol.ServerFactory):
    protocol = ReverserProtocol

class ReverserService(internet.TCPServer):
    def __init__(self):
        internet.TCPServer.__init__(self, 2323, ReverserFactory())

