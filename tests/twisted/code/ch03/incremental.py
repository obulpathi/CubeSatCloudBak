from twisted.protocols import http
from twisted.internet import reactor, defer, protocol
import urlparse, sys, optparse

class HTTPRequest(http.HTTPClient):
    
    def connectionMade(self):
        self.sendCommand('GET', self.factory.path)
        self.sendHeader('Host', self.factory.host)
        self.endHeaders()

    def handleStatus(self, httpVersion, statusCode, message):
        if self.factory.printFullResponse:
            print "%s %s %s" % (httpVersion, statusCode, message)

    def handleHeader(self, header, val):
        if self.factory.printFullResponse:
            print "%s: %s"% (header, val)

    def handleEndHeaders(self):
        if self.factory.printFullResponse:
            print ''

    def handleResponse(self, response):
        print response
    
class HTTPRequestFactory(protocol.ClientFactory):
    protocol = HTTPRequest

    def __init__(self, url, printFullResponse=False):
        self.printFullResponse = printFullResponse
        self.connectionProtocol, self.host, self.path = self.splitUrl(url)
        
    def splitUrl(self, url):
        proto, server, path, params, query, fragment = urlparse.urlparse(url)
        if not proto:
            return self.splitUrl('http://' + url)
        else:
            if not path: path = '/'
            return proto, server, urlparse.urlunparse(
                ('', '', path, params, query, ''))

    def clientConnectionFailed(self, connector, failure):
        print failure.getErrorMessage()
        reactor.stop()

    def clientConnectionLost(self, connector, failure):
        reactor.stop()

if __name__ == "__main__":
    optParser = optparse.OptionParser()
    optParser.add_option('-f',
                         dest='printFullResponse',
                         action="store_true",
                         help='Print full response, including status & headers'
                         )
    options, args = optParser.parse_args()
    if len(args) == 1:
        url = args[0]
        requester = HTTPRequestFactory(url, options.printFullResponse)
        reactor.connectTCP(requester.host, 80, requester)
        reactor.run()
    else:
        optParser.print_help()
        sys.exit(1)
