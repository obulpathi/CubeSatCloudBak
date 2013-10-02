from twisted.web import server, resource, http
import wiki

class RootResource(resource.Resource):
    def __init__(self, wikiData):
        self.wikiData = wikiData
        resource.Resource.__init__(self)
        self.putChild('edit', EditFactory(self.wikiData))
        self.putChild('save', SavePage(self.wikiData))                      

    def getChild(self, path, request):
        return WikiPage(self.wikiData, path or 'WikiHome')

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
        return """
        <html>
        <head><title>Editing: %(path)s</title></head>
        <body>
        Editing: %(path)s
        <form method='post' action='/save'>
        <input type='hidden' name='path' value='%(path)s'>
        <textarea name='data' rows='30' cols='80'>%(data)s</textarea>
        <br />
        <input type='submit' value='Save'>
        </form>
        </body>
        </html>
        """ % {'path':self.path,
               'data':self.wikiData.getPage(self.path)}

class SavePage(resource.Resource):
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
            <a href='/edit/%s'>Edit Page</a> <a href='/'>Home</a>
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

if __name__ == "__main__":
    import sys
    from twisted.internet import reactor
    wikiData = wiki.WikiData(sys.argv[1])
    reactor.listenTCP(8082, server.Site(RootResource(wikiData)))
    reactor.run()
