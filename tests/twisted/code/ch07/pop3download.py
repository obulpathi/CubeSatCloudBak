from twisted.mail import pop3client
from twisted.internet import reactor, protocol, defer
from cStringIO import StringIO
import email

class POP3DownloadProtocol(pop3client.POP3Client):
    # permit logging without encryption
    allowInsecureLogin = True 

    def serverGreeting(self, greeting):
        pop3client.POP3Client.serverGreeting(self, greeting)
        login = self.login(self.factory.username, self.factory.password)
        login.addCallback(self._loggedIn)
        login.chainDeferred(self.factory.deferred)

    def _loggedIn(self, result):
        return self.listSize().addCallback(self._gotMessageSizes)

    def _gotMessageSizes(self, sizes):
        retreivers = []
        for i in range(len(sizes)):
            retreivers.append(self.retrieve(i).addCallback(
                self._gotMessageLines))
        return defer.DeferredList(retreivers).addCallback(
            self._finished)

    def _gotMessageLines(self, messageLines):
        self.factory.handleMessage("\r\n".join(messageLines))

    def _finished(self, downloadResults)
        return self.quit()

class POP3DownloadFactory(protocol.ClientFactory):
    protocol = POP3DownloadProtocol
        
    def __init__(self, username, password, output):
        self.username = username
        self.password = password
        self.output = output
        self.deferred = defer.Deferred()

    def handleMessage(self, messageData):
        parsedMessage = email.message_from_string(messageData)
        self.output.write(parsedMessage.as_string(unixfrom=True))
        self.output.write('\r\n')

    def clientConnectionFailed(self, connection, reason):
        self.deferred.errback(reason)

import sys, getpass

def handleError(error):
    print error
    print >> sys.stderr, "Error:", error.getErrorMessage()
    reactor.stop()

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print "Usage: %s server username output.mbox" % sys.argv[0]
        sys.exit(1)
    else:
        server, username, outputfile = sys.argv[1:]
        password = getpass.getpass("Password: ")
        f = POP3DownloadFactory(username, password, file(outputfile, 'w+b'))
        f.deferred.addCallback(
            lambda _: reactor.stop()).addErrback(
            handleError)
        reactor.connectTCP(server, 110, f)
        reactor.run()

