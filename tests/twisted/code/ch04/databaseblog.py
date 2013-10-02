from twisted.web import resource, static, server, http
from twisted.enterprise import adbapi, util as dbutil

DB_DRIVER = "MySQLdb"
DB_ARGS = {
    'db': 'test',
    'user': 'abe',
    'passwd': 'gear42',
    }

class HomePage(resource.Resource):
    def __init__(self, dbConnection):
        self.db = dbConnection
        resource.Resource.__init__(self)
    
    def render(self, request):
        query = "select title, body from posts order by post_id desc"
        self.db.runQuery(query).addCallback(
            self._gotPosts, request).addErrback(
            self._dbError, request)
        return server.NOT_DONE_YET

    def _gotPosts(self, results, request):
        request.write("""
        <html>
        <head><title>MicroBlog</title></head>
        <body>
          <h1>MicroBlog</h1>
          <i>Like a blog, but less useful</i>
          <p><a href='/new'>New Post</a></p>
        """)

        for title, body in results:
            request.write("<h2>%s</h2>" % title)
            request.write(body)

        request.write("""
        </body>
        </html>
        """)
        request.finish()

    def _dbError(self, failure, request):
        request.setResponseCode(http.INTERNAL_SERVER_ERROR)
        request.write("Error fetching posts: %s" % failure.getErrorMessage())
        request.finish()

class NewPage(resource.Resource):   
    def render(self, request):
        return """
        <html>
        <head><title>New Post</title></head>
        <body>
          <h1>New Post</h1>
          <form action='save' method='post'>
          Title: <input type='text' name='title' /> <br />
          Body: <br />
          <textarea cols='70' name='body'></textarea> <br />
          <input type='submit' value='Save' />
          </form>
        </body>
        </html>
        """

class SavePage(resource.Resource):
    def __init__(self, dbConnection):
        self.db = dbConnection
        resource.Resource.__init__(self)
    
    def render(self, request):
        title = request.args['title'][0]
        body = request.args['body'][0]
        query = """
        Insert into posts (title, body) values (%s, %s)
        """ % (dbutil.quote(title, "char"),
               dbutil.quote(body, "text"))
        self.db.runQuery(query).addCallback(
            self._saved, request).addErrback(
            self._saveFailed, request)
        return server.NOT_DONE_YET
        
    def _saved(self, result, request):
        request.redirect("/")
        request.finish()

    def _saveFailed(self, failure, request):
        request.setResponseCode(http.INTERNAL_SERVER_ERROR)
        request.write("Error saving record: %s" % (
            failure.getErrorMessage()))
        request.finish()
        
class RootResource(resource.Resource):
    def __init__(self, dbConnection):
        resource.Resource.__init__(self)
        self.putChild('', HomePage(dbConnection))
        self.putChild('new', NewPage())
        self.putChild('save', SavePage(dbConnection))

if __name__ == "__main__":
    from twisted.internet import reactor
    dbConnection = adbapi.ConnectionPool(DB_DRIVER, **DB_ARGS)
    f = server.Site(RootResource(dbConnection))
    reactor.listenTCP(8000, f)
    reactor.run()
