from twisted.mail import smtp, maildir
from zope.interface import implements
from twisted.internet import protocol, reactor, defer
import os
from email.Header import Header

class MaildirMessageWriter(object):
    implements(smtp.IMessage)

    def __init__(self, userDir):
        if not os.path.exists(userDir): os.mkdir(userDir)
        inboxDir = os.path.join(userDir, 'Inbox')
        self.mailbox = maildir.MaildirMailbox(inboxDir)
        self.lines = []
    
    def lineReceived(self, line):
        self.lines.append(line)

    def eomReceived(self):
        # message is complete, store it
        print "Message data complete."
        self.lines.append('') # add a trailing newline
        messageData = '\n'.join(self.lines)
        return self.mailbox.appendMessage(messageData)

    def connectionLost(self):
        print "Connection lost unexpectedly!"
        # unexpected loss of connection; don't save
        del(self.lines)

class LocalDelivery(object):
    implements(smtp.IMessageDelivery)

    def __init__(self, baseDir, validDomains):
        if not os.path.isdir(baseDir):
            raise ValueError, "'%s' is not a directory" % baseDir
        self.baseDir = baseDir
        self.validDomains = validDomains
    
    def receivedHeader(self, helo, origin, recipients):
        myHostname, clientIP = helo
        headerValue = "by %s from %s with ESMTP ; %s" % (
            myHostname, clientIP, smtp.rfc822date())
        # email.Header.Header used for automatic wrapping of long lines
        return "Received: %s" % Header(headerValue)

    def validateFrom(self, helo, originAddress):
        # accept mail from anywhere. To reject an address, raise
        # smtp.SMTPBadSender here.
        return originAddress
    
    def validateTo(self, user):
        if not user.dest.domain in self.validDomains:
            raise smtp.SMTPBadRcpt(user)
        print "Accepting mail for %s..." % user.dest
        return lambda: MaildirMessageWriter(
            self._getAddressDir(str(user.dest)))

    def _getAddressDir(self, address):
        return os.path.join(self.baseDir, "%s" % address)
    
class SMTPFactory(protocol.ServerFactory):
    def __init__(self, baseDir, validDomains):
        self.baseDir = baseDir
        self.validDomains = validDomains
    
    def buildProtocol(self, addr):
        delivery = LocalDelivery(self.baseDir, self.validDomains)
        smtpProtocol = smtp.SMTP(delivery)
        smtpProtocol.factory = self
        return smtpProtocol

if __name__ == "__main__":
    import sys
    mailboxDir = sys.argv[1]
    domains = sys.argv[2].split(",")
    reactor.listenTCP(25, SMTPFactory(mailboxDir, domains))
    from twisted.internet import ssl
    # SSL stuff here... and certificates...
    reactor.run()
