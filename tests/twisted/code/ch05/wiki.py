import re, pickle, os
from twisted.web import server, resource, http

reWikiWord = re.compile(r"\b(([A-Z][a-z]+){2,})\b")

class WikiData(object):
    "class for managing Wiki data"
    
    def __init__(self, filename):
        self.filename = filename
        if os.path.exists(filename):
            self.pages = pickle.load(file(filename, 'r+b'))
        else:
            self.pages = {'WikiHome': 'This is your Wiki home page.'}

    def save(self):
        pickle.dump(self.pages, file(self.filename, 'w+b'))

    def hasPage(self, path):
        return self.pages.has_key(path)

    def listPages(self):
        return self.pages.keys()

    def getPage(self, path):
        return self.pages.get(path, '')

    def getRenderedPage(self, path):
        pageData = self.getPage(path)
        "get content with linked WikiWords"
        wikiWords = [match[0] for match in reWikiWord.findall(pageData)]
        for word in wikiWords:
            pageData = pageData.replace(
                word, "<a href='%s'>%s</a>" % (word, word))
        return pageData

    def setPage(self, path, content):
        self.pages[path] = content
        self.save()

    def deletePage(self, path):
        del(self.pages[path])

class WikiPage(resource.Resource):
    def __init__(self, wikiData, path):
        self.wikiData = wikiData
        self.path = path
        resource.Resource.__init__(self)

    def render_GET(self, request):
        if self.wikiData.hasPage(self.path):
            return """
            <html>
            <head><title>%s</title></head>
            <body>
            <p>
            <a href='/edit/%s'>Edit Page</a>
            <a href='/index'>Index</a>
            <a href='/'>Home</a>
            </p>
            %s
            </body>
            </html>
            """ % (self.path, self.path,
                   self.wikiData.getRenderedPage(self.path))
        else:
            request.redirect('/edit/%s' % self.path)
            return ""

    def render_PUT(self, request):
        "accept a PUT request to set the contents of this page"
        if not self.wikiData.hasPage(self.path):
            request.setResponseCode(http.CREATED, "Created new page")
        else:
            request.setResponseCode(http.OK, "Modified existing page")
        request.content.seek(0)
        self.wikiData.setPage(self.path, request.content.read())
        return ""

    def render_DELETE(self, request):
        "accept a DELETE request to remove this page"
        if self.wikiData.hasPage(self.path):
            self.wikiData.deletePage(self.path)
            return "Deleted."
        else:
            request.setResponseCode(http.NOT_FOUND)
            return "No such page."

class EditFactory(resource.Resource):
    def __init__(self, wikiData):
        self.wikiData = wikiData
        resource.Resource.__init__(self)

    def getChild(self, path, request):
        return EditPage(self.wikiData, path)

class EditPage(resource.Resource):
    def __init__(self, wikiData, path):
        self.wikiData = wikiData
        self.path = path
        resource.Resource.__init__(self)
        
    def render(self, request):
        if self.wikiData.hasPage(self.path):
            action = "Editing"
        else:
            action = "Creating"
        return """
        <html>
        <head><title>Editing: %(path)s</title></head>
        <body>
        %(action)s: %(path)s
        <form method='post' action='/save'>
        <input type='hidden' name='path' value='%(path)s'>
        <textarea name='data' rows='30' cols='80'>%(data)s</textarea>
        <br />
        <input type='submit' value='Save'>
        </form>
        </body>
        </html>
        """ % {'path':self.path, 'action': action,
               'data':self.wikiData.getPage(self.path)}

class PageSaverResource(resource.Resource):
    def __init__(self, wikiData):
        self.wikiData = wikiData
        resource.Resource.__init__(self)
        
    def render_POST(self, request):
        data = request.args['data'][0]
        path = request.args['path'][0]
        self.wikiData.setPage(path, data)
        request.redirect('/' + path)
        return ""

    def render_GET(self, request):
        return """
        To add a page to the Wiki, send data to this page using
        HTTP POST. Arguments:
        <ul>
        <li><code>path</code>: the name of a Wiki page</li>
        <li><code>data</code>: the content to use for that page</li>
        </ul>
        """

class IndexPage(resource.Resource):
    def __init__(self, wikiData):
        self.wikiData = wikiData
        resource.Resource.__init__(self)
    
    def render(self, request):
        pages = self.wikiData.listPages()
        pages.sort()
        links = ["<li><a href='%s'>%s</a></li>" % (p, p)
                 for p in pages]
        return """
        <html>
        <head><title>Wiki Index</title></head>
        <a href='/'>Home</a>
        <h1>Index</h1>
        <body>
        <ul>
        %s
        </ul>
        </body>
        """ % "".join(links)

class RootResource(resource.Resource):
    def __init__(self, wikiData):
        self.wikiData = wikiData
        resource.Resource.__init__(self)
        self.putChild('edit', EditFactory(self.wikiData))
        self.putChild('save', PageSaverResource(self.wikiData))
        self.putChild('index', IndexPage(self.wikiData))

    def getChild(self, path, request):
        return WikiPage(self.wikiData, path or 'WikiHome')

if __name__ == "__main__":
    import sys
    from twisted.internet import reactor
    wikiData = WikiData(sys.argv[1])
    reactor.listenTCP(8082, server.Site(RootResource(wikiData)))
    reactor.run()
