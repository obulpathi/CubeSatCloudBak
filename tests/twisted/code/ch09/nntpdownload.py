from twisted.protocols import nntp
from twisted.internet import protocol, defer
import time, email

class NNTPGroupDownloadProtocol(nntp.NNTPClient):

    def connectionMade(self):
        nntp.NNTPClient.connectionMade(self)
        self.fetchGroup(self.factory.newsgroup)

    def gotGroup(self, groupInfo):
        articleCount, first, last, groupName = groupInfo
        first = int(first)
        last = int(last)
        start = max(first, last-self.factory.articleCount)
        self.articlesToFetch = range(start+1, last+1)
        self.articleCount = len(self.articlesToFetch)
        self.fetchNextArticle()

    def fetchNextArticle(self):
        if self.articlesToFetch:
            nextArticleIdx = self.articlesToFetch.pop(0)
            print "Fetching article %i of %i..." % (
                self.articleCount-len(self.articlesToFetch),
                self.articleCount),
            self.fetchArticle(nextArticleIdx)
        else:
            # all done
            self.quit()
            self.factory.deferred.callback(0)

    def gotArticle(self, article):
        print "OK"
        self.factory.handleArticle(article)
        self.fetchNextArticle()

    def getArticleFailed(self, errorMessage):
        print errorMessage
        self.fetchNextArticle()
        
    def getGroupFailed(self, errorMessage):
        self.factory.deferred.errback(Exception(errorMessage))
        self.quit()
        self.transport.loseConnection()

    def connectionLost(self, error):
        if not self.factory.deferred.called:
            self.factory.deferred.errback(error)
    
class NNTPGroupDownloadFactory(protocol.ClientFactory):
    protocol = NNTPGroupDownloadProtocol

    def __init__(self, newsgroup, outputfile, articleCount=10):
        self.newsgroup = newsgroup
        self.articleCount = articleCount
        self.output = outputfile
        self.deferred = defer.Deferred()

    def handleArticle(self, articleData):
        parsedMessage = email.message_from_string(articleData)
        self.output.write(parsedMessage.as_string(unixfrom=True))
        self.output.write('\r\n\r\n')

if __name__ == "__main__":
    from twisted.internet import reactor
    import sys

    def handleError(error):
        print >> sys.stderr, error.getErrorMessage()
        reactor.stop()

    if len(sys.argv) != 4:
        print >> sys.stderr, "Usage: %s nntpserver newsgroup outputfile"
        sys.exit(1)

    server, newsgroup, outfile = sys.argv[1:4]
    factory = NNTPGroupDownloadFactory(newsgroup, file(outfile, 'w+b'))
    factory.deferred.addCallback(
        lambda _: reactor.stop()).addErrback(
        handleError)
    reactor.connectTCP(server, 119, factory)
    reactor.run()
