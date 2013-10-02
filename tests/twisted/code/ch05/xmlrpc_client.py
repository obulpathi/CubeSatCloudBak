from twisted.web import xmlrpc
from twisted.internet import reactor

class WikiTester(object):
    def __init__(self):
        self.wiki = xmlrpc.Proxy('http://localhost:8082/RPC2')

    def runTests(self):
        self.listPages().addCallback(
            lambda _:self.createTestPage()).addCallback(
            lambda _: self.getTestPage()).addErrback(
            self._catchFailure).addCallback(
            lambda _: reactor.stop())

    def listPages(self):
        print "Getting page list..."
        return self.wiki.callRemote('listPages').addCallback(
            self._gotList)

    def _gotList(self, pages):
        print "Got page list:", pages

    def createTestPage(self):
        print "Creating test page XmlRpcTest..."
        pageData = "This is a test of XmlRpc"
        return self.wiki.callRemote('setPage', 'XmlRpcTest', pageData)

    def getTestPage(self):
        print "Getting test page content..."
        return self.wiki.callRemote(
            'getRenderedPage', 'XmlRpcTest').addCallback(
            self._gotTestPage)

    def _gotTestPage(self, content):
        print "Got page content:"
        print content
        return self.listPages()

    def _catchFailure(self, failure):
        print "Error:", failure.getErrorMessage()

w = WikiTester()
w.runTests()
reactor.run()
