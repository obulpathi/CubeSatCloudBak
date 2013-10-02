import wiki
from twisted.web import server, xmlrpc

class WikiXmlRpc(xmlrpc.XMLRPC):
    def __init__(self, wikiData):
        self.wikiData = wikiData

    def xmlrpc_hasPage(self, path):
        return self.wikiData.hasPage(path)

    def xmlrpc_listPages(self):
        return self.wikiData.listPages()

    def xmlrpc_getPage(self, path):
        return self.wikiData.getPage(path)

    def xmlrpc_getRenderedPage(self, path):
        return self.wikiData.getRenderedPage(path)

    def xmlrpc_setPage(self, path, data):
        self.wikiData.setPage(path, data)
        # wikiData.setPage returns None, which has no xmlrpc
        # representation, so you have to return something else
        return path

if __name__ == "__main__":
    import sys
    from twisted.internet import reactor
    datafile = sys.argv[1]
    wikiData = wiki.WikiData(datafile)
    siteRoot = wiki.RootResource(wikiData)
    siteRoot.putChild('RPC2', WikiXmlRpc(wikiData))
    reactor.listenTCP(8082, server.Site(siteRoot))
    reactor.run()
