from twisted.cred import portal, checkers, credentials, error as credError
from twisted.protocols import basic
from twisted.internet import protocol, reactor, defer
from zope.interface import Interface, implements

class PasswordDictChecker(object):
    implements(checkers.ICredentialsChecker)
    credentialInterfaces = (credentials.IUsernamePassword,)

    def __init__(self, passwords):
        "passwords: a dict-like object mapping usernames to passwords"
        self.passwords = passwords

    def requestAvatarId(self, credentials):
        username = credentials.username
        if self.passwords.has_key(username):
            if credentials.password == self.passwords[username]:
                return defer.succeed(username)
            else:
                return defer.fail(
                    credError.UnauthorizedLogin("Bad password"))
        else:
            return defer.fail(
                credError.UnauthorizedLogin("No such user"))

class INamedUserAvatar(Interface):
    "should have attributes username and fullname"

class NamedUserAvatar:
    implements(INamedUserAvatar)
    def __init__(self, username, fullname):
        self.username = username
        self.fullname = fullname

class TestRealm:
    implements(portal.IRealm)

    def __init__(self, users):
        self.users = users

    def requestAvatar(self, avatarId, mind, *interfaces):
        if INamedUserAvatar in interfaces:
            fullname = self.users[avatarId]
            logout = lambda: None
            return (NamedUserAvatar(avatarId, fullname),
                    INamedUserAvatar,
                    logout)
        else:
            raise KeyError("None of the requested interfaces is supported") 
            
class LoginTestProtocol(basic.LineReceiver):
    def lineReceived(self, line):
        cmd = getattr(self, 'handle_' + self.currentCommand)
        cmd(line.strip())

    def connectionMade(self):
        self.transport.write("User Name: ")
        self.currentCommand = 'user'

    def handle_user(self, username):
        self.username = username
        self.transport.write("Password: ")
        self.currentCommand = 'pass'

    def handle_pass(self, password):
        creds = credentials.UsernamePassword(self.username, password)
        self.factory.portal.login(creds, None, INamedUserAvatar).addCallback(
            self._loginSucceeded).addErrback(
            self._loginFailed)

    def _loginSucceeded(self, avatarInfo):
        avatar, avatarInterface, logout = avatarInfo
        self.transport.write("Welcome %s!\r\n" % avatar.fullname)
        defer.maybeDeferred(logout).addBoth(self._logoutFinished)

    def _logoutFinished(self, result):
        self.transport.loseConnection()

    def _loginFailed(self, failure):
        self.transport.write("Denied: %s.\r\n" % failure.getErrorMessage())
        self.transport.loseConnection()
    
class LoginTestFactory(protocol.ServerFactory):
    protocol = LoginTestProtocol

    def __init__(self, portal):
        self.portal = portal

users = {
    'admin': 'Admin User',
    'user1': 'Joe Smith',
    'user2': 'Bob King',
    }

passwords = {
    'admin': 'aaa',
    'user1': 'bbb',
    'user2': 'ccc'
    }

if __name__ == "__main__":
    p = portal.Portal(TestRealm(users))
    p.registerChecker(PasswordDictChecker(passwords))
    factory = LoginTestFactory(p)
    reactor.listenTCP(2323, factory)
    reactor.run()
