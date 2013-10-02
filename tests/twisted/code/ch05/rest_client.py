from twisted.web import client
import urllib

class RestResource(object):
    def __init__(self, uri):
        self.uri = uri

    def get(self):
        return self._sendRequest('GET')

    def post(self, **kwargs):
        postData = urllib.urlencode(kwargs)
        mimeType = 'application/x-www-form-urlencoded'
        return self._sendRequest('POST', postData, mimeType)

    def put(self, data, mimeType):
        return self._sendRequest('PUT', data, mimeType)

    def delete(self):
        return self._sendRequest('DELETE')

    def _sendRequest(self, method, data="", mimeType=None):
        headers = {}
        if mimeType:
            headers['Content-Type'] = mimeType
        if data:
            headers['Content-Length'] = str(len(data))
        return client.getPage(
            self.uri, method=method, postdata=data, headers=headers)

class RestWikiTester(object):
    def __init__(self, baseUri):
        self.baseUri = baseUri

    def test(self):
        return self.createPage("RestTestTmp").addCallback(
            lambda _: self.deletePage("RestTestTmp")).addCallback(
            lambda _: self.createPage("RestTest")).addCallback(
            lambda _: self.getPage("RestTest")).addErrback(
            self.handleFailure)

    def createPage(self, page):
        print "Creating page %s..." % page
        return RestResource(self.baseUri + page).put(
            "Created using HttpPut!", "text/html")

    def deletePage(self, page):
        print "Deleting page %s..." % page
        return RestResource(self.baseUri + page).delete()

    def getPage(self, page):
        uri = self.baseUri + page
        return RestResource(uri).get().addCallback(
            self._gotPage, uri)

    def _gotPage(self, pageData, uri):
        print "Got representation of %s:" % uri
        print pageData
        
    def handleFailure(self, failure):
        print "Error:", failure.getErrorMessage()

if __name__ == "__main__":
    from twisted.internet import reactor
    tester = RestWikiTester('http://localhost:8082/')
    tester.test().addCallback(lambda _: reactor.stop())
    reactor.run()
