from twisted.mail import pop3, maildir
from twisted.cred import portal, checkers, credentials, error as credError
from twisted.internet import protocol, reactor, defer
from zope.interface import implements
import os

class UserInbox(maildir.MaildirMailbox):
    """
    maildir.MaildirMailbox already implements the pop3.IMailbox
    interface, so methods will only need to be defined to
    override the default behavior. For non-maildir mailboxes,
    you'd have to implement all of pop3.IMailbox. 
    """
    def __init__(self, userdir):
        inboxDir = os.path.join(userdir, 'Inbox')
        maildir.MaildirMailbox.__init__(self, inboxDir)

class POP3Protocol(pop3.POP3):
    debug = True
    
    def sendLine(self, line):
        if self.debug: print "POP3 SERVER:", line
        pop3.POP3.sendLine(self, line)

    def lineReceived(self, line):
        if self.debug: print "POP3 CLIENT:", line
        pop3.POP3.lineReceived(self, line)

class POP3Factory(protocol.Factory):
    protocol = POP3Protocol
    portal = None
    
    def buildProtocol(self, address):
        p = self.protocol()
        p.portal = self.portal
        p.factory = self
        return p

class MailUserRealm(object):
    implements(portal.IRealm)
    avatarInterfaces = {
        pop3.IMailbox: UserInbox,
        }

    def __init__(self, baseDir):
        self.baseDir = baseDir

    def requestAvatar(self, avatarId, mind, *interfaces):
        for requestedInterface in interfaces:
            if self.avatarInterfaces.has_key(requestedInterface):
                # make sure the user dir exists
                userDir = os.path.join(self.baseDir, avatarId)
                if not os.path.exists(userDir):
                    os.mkdir(userDir)
                # return an instance of the correct class
                avatarClass = self.avatarInterfaces[requestedInterface]
                avatar = avatarClass(userDir)
                # null logout function: take no arguments and do nothing
                logout = lambda: None
                return defer.succeed((requestedInterface, avatar, logout))
            
        # none of the requested interfaces was supported
        raise KeyError("None of the requested interfaces is supported") 

class CredentialsChecker(object):
    implements(checkers.ICredentialsChecker)
    credentialInterfaces = (credentials.IUsernamePassword,
                            credentials.IUsernameHashedPassword)

    def __init__(self, passwords):
        "passwords: a dict-like object mapping usernames to passwords"
        self.passwords = passwords

    def requestAvatarId(self, credentials):
        username = credentials.username
        if self.passwords.has_key(username):
            realPassword = self.passwords[username]
            checking = defer.maybeDeferred(
                credentials.checkPassword, realPassword)
            # pass result of checkPassword, and the username that was
            # being authenticated, to self._checkedPassword
            checking.addCallback(self._checkedPassword, username)
            return checking
        else:
            raise credError.UnauthorizedLogin("No such user")
            
    def _checkedPassword(self, matched, username):
        if matched:
            # password was correct
            return username
        else:
            raise credError.UnauthorizedLogin("Bad password")

def passwordFileToDict(filename):
    passwords = {}
    for line in file(filename):
        if line and line.count(':'):
            username, password = line.strip().split(':')
            passwords[username] = password
    return passwords
    
if __name__ == "__main__":
    import sys
    dataDir = sys.argv[1]
    factory = POP3Factory()
    factory.portal = portal.Portal(MailUserRealm(dataDir))
    passwordFile = os.path.join(dataDir, 'passwords.txt')
    passwords = passwordFileToDict(passwordFile)
    passwordChecker = CredentialsChecker(passwords)
    factory.portal.registerChecker(passwordChecker)
    reactor.listenTCP(110, factory)
    reactor.run()
