from twisted.protocols import imap4
from twisted.internet import protocol, defer

class IMAPFolderListProtocol(imap4.IMAP4Client):

    def serverGreeting(self, capabilities):
        self.registerAuthenticator(
            imap4.CramMD5ClientAuthenticator(self.factory.username))
        self.registerAuthenticator(
            imap4.LOGINAuthenticator(self.factory.username))
        authenticating = self.authenticate(self.factory.password)
        authenticating.addCallback(self.__loggedIn)
        authenticating.chainDeferred(self.factory.deferred)

    def __loggedIn(self, results):
        return self.list("", "*").addCallback(self.__gotMailboxList)

    def __gotMailboxList(self, list):
        return [boxInfo[2] for boxInfo in list]

    def connectionLost(self, reason):
        if not self.factory.deferred.called:
            # connection was lost unexpectedly!
            self.factory.deferred.errback(reason)

class IMAPFolderListFactory(protocol.ClientFactory):
    protocol = IMAPFolderListProtocol
    
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.deferred = defer.Deferred()
        
    def clientConnectionFailed(self, connection, reason):
        self.deferred.errback(reason)

if __name__ == "__main__":
    from twisted.internet import reactor
    import sys, getpass
    
    def printMailboxList(list):
        list.sort()
        for box in list:
            print box
        reactor.stop()

    def handleError(error):
        print >> sys.stderr, "Error:", error.getErrorMessage()
        reactor.stop()

    if not len(sys.argv) == 3:
        print "Usage: %s server login" % sys.argv[0]
        sys.exit(1)
        
    server = sys.argv[1]
    user = sys.argv[2]
    password = getpass.getpass("Password: ")
    factory = IMAPFolderListFactory(user, password)
    factory.deferred.addCallback(
        printMailboxList).addErrback(
        handleError)
    reactor.connectTCP(server, 143, factory)
    reactor.run()
