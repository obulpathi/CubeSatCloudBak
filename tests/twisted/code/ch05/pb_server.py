from twisted.spread import pb
import wiki    

class WikiPerspective(pb.Root):
    def __init__(self, wikiData):
        self.wikiData = wikiData

    def remote_hasPage(self, path):
        return self.wikiData.hasPage(path)

    def remote_listPages(self):
        return self.wikiData.listPages()

    def remote_getPage(self, path):
        return self.wikiData.getPage(path)

    def remote_getRenderedPage(self, path):
        return self.wikiData.getRenderedPage(path)

    def remote_setPage(self, path, data):
        self.wikiData.setPage(path, data)

    def remote_getReporter(self):
        return WikiReporter(self.wikiData)

class WikiReporter(pb.Referenceable):
    "I do simple reporting tasks in the wiki"
    def __init__(self, wikiData):
        self.pages = wikiData.pages
        
    def remote_listNeededPages(self):
        "return a list of pages that are linked to but don't exist yet"
        neededPages = []
        for page in self.pages.values():
            wikiWords = [match[0]
                         for match in wiki.reWikiWord.findall(page)]
            for pageName in wikiWords:
                if not self.pages.has_key(pageName):
                    neededPages.append(pageName)
        return neededPages

if __name__ == "__main__":
    import sys
    from twisted.internet import reactor
    datafile = sys.argv[1]
    wikiData = wiki.WikiData(datafile)
    wikiPerspective = WikiPerspective(wikiData)
    reactor.listenTCP(8789, pb.PBServerFactory(wikiPerspective))
    reactor.run()
