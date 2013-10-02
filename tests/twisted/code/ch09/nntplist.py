from twisted.protocols import nntp
from twisted.internet import protocol, defer

class NNTPGroupListerProtocol(nntp.NNTPClient):

    def connectionMade(self):
        nntp.NNTPClient.connectionMade(self)
        self.fetchGroups()

    def gotAllGroups(self, groups):
        groupnames = [groupInfo[0] for groupInfo in groups]
        self.factory.deferred.callback(groupnames)
        self.quit()

    def getAllGroupsFailed(self, error):
        self.factory.deferred.errback(error)

    def connectionLost(self, error):
        if not self.factory.deferred.called:
            self.factory.deferred.errback(error)
    
class NNTPGroupListerFactory(protocol.ClientFactory):
    protocol = NNTPGroupListerProtocol

    def __init__(self):
        self.deferred = defer.Deferred()

if __name__ == "__main__":
    from twisted.internet import reactor
    import sys

    def printGroups(groups):
        for group in groups:
            print group
        reactor.stop()

    def handleError(error):
        print >> sys.stderr, error.getErrorMessage()
        reactor.stop()

    if not len(sys.argv) == 2:
        print "Usage: %s server" % sys.argv[0]
        sys.exit(1)
        
    server = sys.argv[1]
    factory = NNTPGroupListerFactory()
    factory.deferred.addCallback(printGroups).addErrback(handleError)
    
    reactor.connectTCP(server, 119, factory)
    reactor.run()
