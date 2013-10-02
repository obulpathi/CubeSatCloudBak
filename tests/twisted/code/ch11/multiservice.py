from twisted.application import service, internet
from twisted.internet import protocol, reactor, defer
from twisted.protocols import basic
from twisted.web import resource, server as webserver

class Reverser:
    def __init__(self):
        self.history = []
    
    def reverse(self, string):
        self.history.append(string)
        reversed = string[::-1]
        return reversed

class ReverserLineProtocol(basic.LineReceiver):
    def lineReceived(self, line):
        if hasattr(self, 'handle_' + line):
            getattr(self, 'handle_' + line)()
        else:
            self.sendLine(self.factory.reverser.reverse(line))

    def handle_quit(self):
        self.transport.loseConnection()

class ReverserLineFactory(protocol.ServerFactory):
    protocol = ReverserLineProtocol
    
    def __init__(self, reverser):
        self.reverser = reverser

class ReverserPage(resource.Resource):
    def __init__(self, reverser):
        self.reverser = reverser
        
    def render(self, request):
        if request.args.has_key("string"):
            string = request.args["string"][0]
            reversed = self.reverser.reverse(string)
        else:
            reversed = ""

        return """
        <html><body><form>
        <input type='text' name='string' value='%s' />
        <input type='submit' value='Go' />
        <h2>Previous Strings</h2>
        <ul>
        %s
        </ul>
        </form></body></html>
        """ % (reversed,
               "\n".join(["<li>%s</li>" % s for s in self.reverser.history]))

class ServiceAdminPage(resource.Resource):
    def __init__(self, app):
        self.app = app

    def render_GET(self, request):
        request.write("""
        <html><body>
        <h1>Current Services</h1>
        <form method='post'>
        <ul>
        """)
        for srv in service.IServiceCollection(self.app):
            if srv.running:
                checked = "checked='checked'"
            else:
                checked = ""
            request.write("""
            <input type='checkbox' %s name='service' value='%s'>%s<br />
            """ % (checked, srv.name, srv.name))
        request.write("""
        <input type='submit' value='Go' />
        </form>
        </body></html>
        """)
        return ''

    def render_POST(self, request):
        actions = []
        serviceList = request.args.get('service', [])
        for srv in service.IServiceCollection(self.app):
            if srv.running and not srv.name in serviceList:
                stopping = defer.maybeDeferred(srv.stopService)
                actions.append(stopping)
            elif not srv.running and srv.name in serviceList:
                # wouldn't work if this program were using reserved ports
                # and running under an unprivileged user id
                starting = defer.maybeDeferred(srv.startService)
                actions.append(starting)
        defer.DeferredList(actions).addCallback(
            self._finishedActions, request)
        return webserver.NOT_DONE_YET

    def _finishedActions(self, results, request):
        request.redirect('/')
        request.finish()

application = service.Application("Reverser")
reverser = Reverser()

lineService = internet.TCPServer(2323, ReverserLineFactory(reverser))
lineService.setName("Telnet")
lineService.setServiceParent(application)

webRoot = resource.Resource()
webRoot.putChild('', ReverserPage(reverser))
webService = internet.TCPServer(8000, webserver.Site(webRoot))
webService.setName("Web")
webService.setServiceParent(application)

webAdminRoot = resource.Resource()
webAdminRoot.putChild('', ServiceAdminPage(application))
webAdminService = internet.TCPServer(8001, webserver.Site(webAdminRoot))
webAdminService.setName("WebAdmin")
webAdminService.setServiceParent(application)


