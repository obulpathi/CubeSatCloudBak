from twisted.mail import smtp
from twisted.web import google, client
from zope.interface import implements
from twisted.internet import protocol, reactor, defer
import os, email, email.Utils
from email import Header, MIMEBase, MIMEMultipart, MIMEText

class GoogleQueryPageFetcher(object):
    def fetchFirstResult(self, query):
        """
        Given a query, find the first Google result, and
        downloads that page. Returns a Deferred which will
        be called back with a tuple containing
        (firstMatchUrl, firstMatchPageData)
        """
        # the twisted.web.google.checkGoogle function does an
        # "I'm feeling lucky" search on Google
        return google.checkGoogle(query).addCallback(
            self._gotUrlFromGoogle)

    def _gotUrlFromGoogle(self, url):
        # grab the page
        return client.getPage(url).addCallback(
            self._downloadedPage, url)

    def _downloadedPage(self, pageContents, url):
        # return a tuple containing both the url and page data
        return (url, pageContents)

class ReplyFromGoogle(object):
    implements(smtp.IMessage)

    def __init__(self, address, upstreamServer):
        self.address = address
        self.lines = []
        self.upstreamServer = upstreamServer

    def lineReceived(self, line):
        self.lines.append(line)

    def eomReceived(self):
        message = email.message_from_string("\n".join(self.lines))
        fromAddr = email.Utils.parseaddr(message['From'])[1]
        query = message['Subject']
        searcher = GoogleQueryPageFetcher()
        return searcher.fetchFirstResult(query).addCallback(
            self._sendPageToEmailAddress, query, fromAddr)

    def _sendPageToEmailAddress(self, pageData, query, destAddress):
        pageUrl, pageContents = pageData
        msg = MIMEMultipart.MIMEMultipart()
        msg['From'] = self.address
        msg['To'] = destAddress
        msg['Subject'] = "First Google result for '%s'" % query
        body = MIMEText.MIMEText(
            "The first Google result for '%s' is:\n\n%s" % (
            query, pageUrl))
        # create a text/html attachment with the page data
        attachment = MIMEBase.MIMEBase("text", "html")
        attachment['Content-Location'] = pageUrl
        attachment.set_payload(pageContents)
        msg.attach(body)
        msg.attach(attachment)
        
        return smtp.sendmail(
            self.upstreamServer, self.address, destAddress, msg)

    def connectionLost(self):
        pass
    
class GoogleMessageDelivery(object):
    implements(smtp.IMessageDelivery)

    def __init__(self, googleSearchAddress, upstreamSMTPServer):
        self.googleSearchAddress = googleSearchAddress
        self.upstreamServer = upstreamSMTPServer
    
    def receivedHeader(self, helo, origin, recipients):
        myHostname, clientIP = helo
        headerValue = "by %s from %s with ESMTP ; %s" % (
            myHostname, clientIP, smtp.rfc822date())
        # email.Header.Header used for automatic wrapping of long lines
        return "Received: %s" % Header.Header(headerValue)
    
    def validateTo(self, user):
        if not str(user.dest).lower() == self.googleSearchAddress:
            raise smtp.SMTPBadRcpt(user.dest)
        else:
            return lambda: ReplyFromGoogle(self.googleSearchAddress,
                                           self.upstreamServer)
    
    def validateFrom(self, helo, originAddress):
        # accept mail from anywhere. To reject an address, raise
        # smtp.SMTPBadSender here.
        return originAddress

class SMTPServerFactory(protocol.ServerFactory):
    def __init__(self, googleSearchAddress, upstreamSMTPServer):
        self.googleSearchAddress = googleSearchAddress
        self.upstreamSMTPServer = upstreamSMTPServer
    
    def buildProtocol(self, addr):
        delivery = GoogleMessageDelivery(self.googleSearchAddress,
                                         self.upstreamSMTPServer)
        smtpProtocol = smtp.SMTP(delivery)
        smtpProtocol.factory = self
        return smtpProtocol

if __name__ == "__main__":
    import sys
    googleSearchAddress = sys.argv[1]
    upstreamSMTPServer = sys.argv[2]
    reactor.listenTCP(
        25, SMTPServerFactory(googleSearchAddress, upstreamSMTPServer))
    reactor.run()
