from twisted.spread import pb
from twisted.internet import reactor
from twisted.cred import credentials

class PbAuthTester(object):
    def __init__(self, credentials):
        self.credentials = credentials
        self.server = None

    def runTests(self):
        self.connect().addCallback(
            lambda _: self.listItems()).addCallback(
            lambda _: self.addItem()).addErrback(
            self._catchFailure).addCallback(
            lambda _: reactor.stop())

    def connect(self):
        factory = pb.PBClientFactory()
        reactor.connectTCP("localhost", 8789, factory)
        return factory.login(self.credentials).addCallback(self._connected)

    def _connected(self, rootObj):
        self.server = rootObj

    def listItems(self):
        print "Getting item list..."
        return self.server.callRemote("listItems").addCallback(self._gotList)

    def _gotList(self, list):
        print "%i items in list." % (len(list))

    def addItem(self):
        print "Adding new item..."
        return self.server.callRemote(
            "addItem", "Buy groceries").addCallback(
            self._addedItem)

    def _addedItem(self, result):
        print "Added 1 item."

    def _catchFailure(self, failure):
        print "Error:", failure.getErrorMessage()

if __name__ == "__main__":
    import sys
    username, password = sys.argv[1:3]
    creds = credentials.UsernamePassword(username, password)
    tester = PbAuthTester(creds)
    tester.runTests()
    reactor.run()
