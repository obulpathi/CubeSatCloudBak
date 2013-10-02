from twisted.web import soap
from twisted.internet import reactor

class DebugProxy(soap.Proxy):
    def _cbGotResult(self, result):
        print result
        return soap.Proxy._cbGotResult(self, result)

class WikiTester(object):
    def __init__(self):
        self.wiki = DebugProxy('http://localhost:8082/SOAP')

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
        print "Creating test page SoapTest..."
        pageData = "This is a test of SoapRpc"
        return self.wiki.callRemote('setPage', 'SoapTest', pageData)

    def getTestPage(self):
        print "Getting test page content..."
        return self.wiki.callRemote(
            'getRenderedPage', 'SoapTest').addCallback(
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
