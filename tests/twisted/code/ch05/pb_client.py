from twisted.spread import pb
from twisted.internet import reactor

class PbTester(object):
    def __init__(self):
        self.wiki = None

    def runTests(self):
        self.connect().addCallback(
            lambda _: self.listPages()).addCallback(
            lambda _: self.createTestPage()).addCallback(
            lambda _: self.getTestPage()).addCallback(
            lambda _: self.runReports()).addErrback(
            self._catchFailure).addCallback(
            lambda _: reactor.stop())

    def connect(self):
        factory = pb.PBClientFactory()
        reactor.connectTCP("localhost", 8789, factory)
        return factory.getRootObject().addCallback(self._connected)

    def _connected(self, rootObj):
        self.wiki = rootObj

    def listPages(self):
        print "Getting page list..."
        return self.wiki.callRemote('listPages').addCallback(
            self._gotList)

    def _gotList(self, pages):
        print "Got page list:", pages

    def createTestPage(self):
        print "Creating test page PbTest..."
        pageData = "This is a test of PerspectiveBroker"
        return self.wiki.callRemote('setPage', 'PbTest', pageData)

    def getTestPage(self):
        print "Getting test page content..."
        return self.wiki.callRemote(
            'getRenderedPage', 'PbTest').addCallback(
            self._gotTestPage)

    def _gotTestPage(self, content):
        print "Got page content:"
        print content
        return self.listPages()

    def runReports(self):
        print "Running report..."
        return self.wiki.callRemote('getReporter').addCallback(
            self._gotReporter)

    def _gotReporter(self, reporter):
        print "Got remote reporter object"
        return reporter.callRemote('listNeededPages').addCallback(
            self._gotNeededPages)

    def _gotNeededPages(self, pages):
        print "These pages are needed:", pages

    def _catchFailure(self, failure):
        print "Error:", failure.getErrorMessage()

t = PbTester()
t.runTests()
reactor.run()
