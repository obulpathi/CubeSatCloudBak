from twisted.protocols import imap4
from twisted.internet import protocol, defer
import email

class IMAPDownloadProtocol(imap4.IMAP4Client):

    def serverGreeting(self, capabilities):
        login = self.login(self.factory.username, self.factory.password)
        login.addCallback(self.__loggedIn)
        login.chainDeferred(self.factory.deferred)

    def __loggedIn(self, result):
        return self.select(self.factory.mailbox).addCallback(
            self.__selectedMailbox)

    def __selectedMailbox(self, result):
        # get a list of all message IDs
        allMessages = imap4.MessageSet(1, None)
        return self.fetchUID(allMessages, True).addCallback(
            self.__gotUIDs)

    def __gotUIDs(self, uidResults):
        self.messageUIDs = [result['UID'] for result in uidResults.values()]
        self.messageCount = len(self.messageUIDs)
        print "%i messages in %s." % (self.messageCount, self.factory.mailbox)
        return self.fetchNextMessage()

    def fetchNextMessage(self):
        if self.messageUIDs:
            nextUID = self.messageUIDs.pop(0)
            messageListToFetch = imap4.MessageSet(nextUID)
            print "Downloading message %i of %i" % (
                self.messageCount-len(self.messageUIDs), self.messageCount)
            return self.fetchMessage(messageListToFetch, uid=True).addCallback(
                self.__gotMessage)
        else:
            # all done!
            return self.logout().addCallback(
                lambda _: self.transport.loseConnection())

    def __gotMessage(self, fetchResults):
        messageData = fetchResults.values()[0]['RFC822']
        self.factory.handleMessage(messageData)
        return self.fetchNextMessage()

    def connectionLost(self, reason):
        if not self.factory.deferred.called:
            # connection was lost unexpectedly!
            self.factory.deferred.errback(reason)

class IMAPDownloadFactory(protocol.ClientFactory):
    protocol = IMAPDownloadProtocol
    
    def __init__(self, username, password, mailbox, output):
        self.username = username
        self.password = password
        self.mailbox = mailbox
        self.output = output
        self.deferred = defer.Deferred()

    def handleMessage(self, messageData):
        parsedMessage = email.message_from_string(messageData)
        self.output.write(parsedMessage.as_string(unixfrom=True))
        self.output.write('\r\n')
        
    def clientConnectionFailed(self, connection, reason):
        self.deferred.errback(reason)

if __name__ == "__main__":
    from twisted.internet import reactor
    import sys, getpass

    def handleError(error):
        print >> sys.stderr, "Error:", error.getErrorMessage()
        reactor.stop()

    if len(sys.argv) != 5:
        usage = "Usage: %s server user mailbox outputfile" % (
            sys.argv[0])
        print >> sys.stderr, usage
        sys.exit(1)

    server = sys.argv[1]
    user = sys.argv[2]
    mailbox = sys.argv[3]
    outputfile = file(sys.argv[4], 'w+b')

    password = getpass.getpass("Password: ")
    factory = IMAPDownloadFactory(user, password, mailbox, outputfile)
    factory.deferred.addCallback(lambda _: reactor.stop()).addErrback(
        handleError)
    reactor.connectTCP(server, 143, factory)
    reactor.run()
