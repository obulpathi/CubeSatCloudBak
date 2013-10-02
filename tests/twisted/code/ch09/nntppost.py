from twisted.news import nntp
from twisted.internet import protocol, defer
import time, email

class NNTPPostProtocol(nntp.NNTPClient):

    def connectionMade(self):
        nntp.NNTPClient.connectionMade(self)
        # post the article
        self.postArticle(self.factory.articleData)

    def postedOk(self):
        self.factory.deferred.callback(None)

    def postFailed(self, errorMessage):
        self.factory.deferred.errback(Exception(errorMessage))

    def connectionLost(self, error):
        if not self.factory.deferred.called:
            self.factory.deferred.errback(error)
    
class NNTPPostFactory(protocol.ClientFactory):
    protocol = NNTPPostProtocol

    def __init__(self, newsgroup, articleData):
        self.newsgroup = newsgroup
        self.articleData = articleData
        self.deferred = defer.Deferred()

from email.Message import Message
from email.Utils import make_msgid, formatdate()

def makeArticle(sender, newsgroup, subject, body):
    article = Message()
    article["From"] = sender
    article["Newsgroups"] = newsgroup
    article["Subject"] = subject
    article["Message-Id"] = make_msgid()
    article["Date"] = formatdate()
    article.set_payload(body)
    return article.as_string(unixfrom=False)

if __name__ == "__main__":
    from twisted.internet import reactor
    import sys

    def handleError(error):
        print >> sys.stderr, error.getErrorMessage()
        reactor.stop()

    if len(sys.argv) != 3:
        print >> sys.stderr, "Usage: %s server newsgroup" % sys.argv[0]
        sys.exit(1)

    server, newsgroup = sys.argv[1:3]
    sender = raw_input("From: ")
    subject = raw_input("Subject: ")
    print "Enter article body below, followed by a single period:"
    bodyLines = []
    while True:
        line = raw_input()
        if line == ".": break
        bodyLines.append(line)
    body = "\n".join(bodyLines)
    articleData = makeArticle(sender, newsgroup, subject, body)
    print articleData
    factory = NNTPPostFactory(newsgroup, articleData)
    factory.deferred.addCallback(
        lambda _: reactor.stop()).addErrback(
        handleError)
    reactor.connectTCP(server, 119, factory)
    reactor.run()
