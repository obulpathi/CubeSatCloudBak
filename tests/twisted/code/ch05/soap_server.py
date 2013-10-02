import wiki
from twisted.web import server, soap

class WikiSoap(soap.SOAPPublisher):

    def render(self, request, *args):
        request.content.seek(0)
        print request.content.read()
        request.content.seek(0)
        soap.SOAPPublisher.render(self, request, *args)
    
    def __init__(self, wikiData):
        self.wikiData = wikiData

    def soap_hasPage(self, path):
        return self.wikiData.hasPage(path)

    def soap_listPages(self):
        return self.wikiData.listPages()

    def soap_getPage(self, path):
        return self.wikiData.getPage(path)

    def soap_getRenderedPage(self, path):
        return self.wikiData.getRenderedPage(path)

    def soap_setPage(self, path, data):
        self.wikiData.setPage(path, data)

if __name__ == "__main__":
    import sys
    from twisted.internet import reactor
    datafile = sys.argv[1]
    wikiData = wiki.WikiData(datafile)
    siteRoot = wiki.RootResource(wikiData)
    siteRoot.putChild('SOAP', WikiSoap(wikiData))
    reactor.listenTCP(8082, server.Site(siteRoot))
    reactor.run()
