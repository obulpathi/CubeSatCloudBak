import sgmllib, re
from twisted.web import proxy, http
import sys
from twisted.python import log
log.startLogging(sys.stdout)

WEB_PORT = 8000
PROXY_PORT = 8001

# classes for parsing HTML and keeping track of word counts

class WordParser(sgmllib.SGMLParser):
    def __init__(self):
        sgmllib.SGMLParser.__init__(self)
        self.chardata = []
        self.inBody = False

    def start_body(self, attrs):
        self.inBody = True

    def end_body(self):
        self.inBody = False
        
    def handle_data(self, data):
        if self.inBody: 
            self.chardata.append(data)

    def getWords(self):
        # extract words
        wordFinder = re.compile(r'\w*')
        words = wordFinder.findall("".join(self.chardata))
        words = filter(lambda word: word.strip(), words)
        return words

class WordCounter(object):
    ignoredWords = "the a of in from to this that and or but is was be can could i you they we at".split()

    def __init__(self):
        self.words = {}
    
    def addWords(self, words):
        for word in words:
            word = word.lower()
            if not word in self.ignoredWords:
                currentCount = self.words.get(word, 0)
                self.words[word] = currentCount + 1

# proxy server classes

class WordCountProxyClient(proxy.ProxyClient):
    def handleHeader(self, key, value):
        proxy.ProxyClient.handleHeader(self, key, value)
        if key.lower() == "content-type":
            if value.split(';')[0] == 'text/html':
                self.parser = WordParser()

    def handleResponsePart(self, data):
        proxy.ProxyClient.handleResponsePart(self, data)
        if hasattr(self, 'parser'): self.parser.feed(data)

    def handleResponseEnd(self):
        proxy.ProxyClient.handleResponseEnd(self)
        if hasattr(self, 'parser'):
            self.parser.close()
            self.father.wordCounter.addWords(self.parser.getWords())
            del(self.parser)

class WordCountProxyClientFactory(proxy.ProxyClientFactory):
    def buildProtocol(self, addr):
        client = proxy.ProxyClientFactory.buildProtocol(self, addr)
        # upgrade proxy.proxyClient object to WordCountProxyClient
        client.__class__ = WordCountProxyClient
        return client
            
class WordCountProxyRequest(proxy.ProxyRequest):
    protocols = {'http': WordCountProxyClientFactory}
    
    def __init__(self, wordCounter, *args):
        self.wordCounter = wordCounter
        proxy.ProxyRequest.__init__(self, *args)

class WordCountProxy(proxy.Proxy):
    def __init__(self, wordCounter):
        self.wordCounter = wordCounter
        proxy.Proxy.__init__(self)

    def requestFactory(self, *args):
        return WordCountProxyRequest(self.wordCounter, *args)

class WordCountProxyFactory(http.HTTPFactory):
    def __init__(self, wordCounter):
        self.wordCounter = wordCounter
        http.HTTPFactory.__init__(self)
        
    def buildProtocol(self, addr):
        protocol = WordCountProxy(self.wordCounter)
        return protocol

# classes for web reporting interface

class WebReportRequest(http.Request):
    def __init__(self, wordCounter, *args):
        self.wordCounter = wordCounter
        http.Request.__init__(self, *args)
    
    def process(self):
        self.setHeader("Content-Type", "text/html")
        words = self.wordCounter.words.items()
        words.sort(lambda (w1, c1), (w2, c2): cmp(c2, c1))
        self.write("<html><body><h1>Word List</h1><ul>")
        for word, count in words:
            self.write("<li>%s (%s)</li>" % (word, count))
        self.write("</ul></body></html>")
        self.finish()

class WebReportChannel(http.HTTPChannel):
    def __init__(self, wordCounter):
        self.wordCounter = wordCounter
        http.HTTPChannel.__init__(self)
    
    def requestFactory(self, *args):
        return WebReportRequest(self.wordCounter, *args)

class WebReportFactory(http.HTTPFactory):
    def __init__(self, wordCounter):
        self.wordCounter = wordCounter
        http.HTTPFactory.__init__(self)

    def buildProtocol(self, addr):
        return WebReportChannel(self.wordCounter)
        
if __name__ == "__main__":
    from twisted.internet import reactor
    counter = WordCounter()
    prox = WordCountProxyFactory(counter)
    reactor.listenTCP(PROXY_PORT, prox)
    reactor.listenTCP(WEB_PORT, WebReportFactory(counter))
    reactor.run()
