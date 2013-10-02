from twisted.web import client

class HTTPStatusChecker(client.HTTPClientFactory):

    def __init__(self, url, headers=None):
        client.HTTPClientFactory.__init__(self, url, headers=headers)
        self.status = None
        self.deferred.addCallback(
            lambda data: (data, self.status, self.response_headers))

    def noPage(self, reason): # called for non-200 responses
        if self.status == '304': # Page hadn't changed
            client.HTTPClientFactory.page(self, '')
        else:
            client.HTTPClientFactory.noPage(self, reason)

def checkStatus(url, contextFactory=None, *args, **kwargs):
    scheme, host, port, path = client._parse(url)
    factory = HTTPStatusChecker(url, *args, **kwargs)
    if scheme == 'https':
        from twisted.internet import ssl
        if contextFactory is None:
            contextFactory = ssl.ClientContextFactory()
        reactor.connectSSL(host, port, factory, contextFactory)
    else:
        reactor.connectTCP(host, port, factory)
    return factory.deferred

def handleFirstResult(result, url):
    data, status, headers = result
    nextRequestHeaders = {}
    eTag = headers.get('etag')
    if eTag:
        nextRequestHeaders['If-None-Match'] = eTag[0]
    modified = headers.get('last-modified')
    if modified:
        nextRequestHeaders['If-Modified-Since'] = modified[0]
    return checkStatus(url, headers=nextRequestHeaders).addCallback(
        handleSecondResult)

def handleSecondResult(result):
    data, status, headers = result
    print 'Second request returned status %s:' % status,
    if status == '200':
        print 'Page changed (or server does not support conditional requests).'
    elif status == '304':
        print 'Page is unchanged.'
    else:
        print 'Unexpected Response.'
    reactor.stop()

def handleError(failure):
    print "Error", failure.getErrorMessage()
    reactor.stop()

if __name__ == "__main__":
    import sys
    from twisted.internet import reactor

    url = sys.argv[1]
    checkStatus(url).addCallback(
        handleFirstResult, url).addErrback(
        handleError)
    reactor.run()
