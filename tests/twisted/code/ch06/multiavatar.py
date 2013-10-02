from twisted.cred import portal, checkers, credentials, error as credError
from twisted.protocols import basic
from twisted.internet import protocol, reactor, defer
from zope.interface import Interface, implements

class INamedUserAvatar(Interface):
    "should have attributes username and fullname"

class NamedUserAvatar:
    implements(INamedUserAvatar)
    def __init__(self, username, fullname):
        self.username = username
        self.fullname = fullname

class INewUserAvatar(Interface):
    "should have username attribute only"
    def setName(self, fullname):
        raise NotImplementedError

class NewUserAvatar:
    implements(INewUserAvatar)
    def __init__(self, username, userDb):
        self.username = username
        self.userDb = userDb

    def setName(self, fullname):
        self.userDb[self.username] = fullname
        return NamedUserAvatar(self.username, fullname)

class MultiAvatarRealm:
    implements(portal.IRealm)

    def __init__(self, users):
        self.users = users

    def requestAvatar(self, avatarId, mind, *interfaces):
        logout = lambda: None
        if INamedUserAvatar in interfaces and self.users.has_key(avatarId):
            fullname = self.users[avatarId]
            return (NamedUserAvatar(avatarId, fullname),
                    INamedUserAvatar,
                    logout)
        elif INewUserAvatar in interfaces:
            avatar = NewUserAvatar(avatarId, self.users)
            return (avatar, INewUserAvatar, logout)
        else:
            raise KeyError("None of the requested interfaces is supported") 
            
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
            
class NamedUserLoginProtocol(basic.LineReceiver):
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
        avatarInterfaces = (INamedUserAvatar, INewUserAvatar)
        self.factory.portal.login(creds, None, *avatarInterfaces).addCallback(
            self._loginSucceeded).addErrback(
            self._loginFailed)

    def _loginSucceeded(self, avatarInfo):
        avatar, avatarInterface, self.logout = avatarInfo
        if avatarInterface == INewUserAvatar:
            self.transport.write("What's your full name? ")
            self.currentCommand = "fullname"
            self.avatar = avatar
        else:
            self._gotNamedUser(avatar)

    def handle_fullname(self, fullname):
        namedUserAvatar = self.avatar.setName(fullname)
        self._gotNamedUser(namedUserAvatar)

    def _gotNamedUser(self, avatar):
        self.transport.write("Welcome %s!\r\n" % avatar.fullname)
        defer.maybeDeferred(self.logout).addBoth(self._logoutFinished)

    def _logoutFinished(self, result):
        self.transport.loseConnection()

    def _loginFailed(self, failure):
        self.transport.write("Denied: %s.\r\n" % failure.getErrorMessage())
        self.transport.loseConnection()
    
class NamedUserLoginFactory(protocol.ServerFactory):
    protocol = NamedUserLoginProtocol

    def __init__(self, portal):
        self.portal = portal

users = {
    'admin': 'Admin User',
    }

passwords = {
    'admin': 'aaa',
    'user1': 'bbb',
    'user2': 'ccc'
    }

portal = portal.Portal(MultiAvatarRealm(users))
portal.registerChecker(PasswordDictChecker(passwords))
factory = NamedUserLoginFactory(portal)
reactor.listenTCP(2323, factory)
reactor.run()
