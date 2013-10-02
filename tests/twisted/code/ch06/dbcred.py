from twisted.enterprise import adbapi, util as dbutil
from twisted.cred import credentials, portal, checkers, error as credError
from twisted.internet import reactor, defer
from zope.interface import implements
import simplecred

class DbPasswordChecker(object):
    implements(checkers.ICredentialsChecker)
    credentialInterfaces = (credentials.IUsernamePassword,
                            credentials.IUsernameHashedPassword)

    def __init__(self, dbconn):
        self.dbconn = dbconn

    def requestAvatarId(self, credentials):
        query = "select userid, password from user where username = %s" % (
            dbutil.quote(credentials.username, "char"))
        return self.dbconn.runQuery(query).addCallback(
            self._gotQueryResults, credentials)

    def _gotQueryResults(self, rows, userCredentials):
        if rows:
            userid, password = rows[0]
            return defer.maybeDeferred(
                userCredentials.checkPassword, password).addCallback(
                self._checkedPassword, userid)
        else:
            raise credError.UnauthorizedLogin, "No such user"
              
    def _checkedPassword(self, matched, userid):
        if matched:
            return userid
        else:
            raise credError.UnauthorizedLogin("Bad password")

class DbRealm:
    implements(portal.IRealm)

    def __init__(self, dbconn):
        self.dbconn = dbconn

    def requestAvatar(self, avatarId, mind, *interfaces):
        if simplecred.INamedUserAvatar in interfaces:
            userQuery = """
              select username, firstname, lastname
              from user where userid = %s
            """ % dbutil.quote(avatarId, "int")
            return self.dbconn.runQuery(userQuery).addCallback(
                self._gotQueryResults)
        else:
            raise KeyError("None of the requested interfaces is supported") 

    def _gotQueryResults(self, rows):
        username, firstname, lastname = rows[0]
        fullname = "%s %s" % (firstname, lastname)
        return (simplecred.NamedUserAvatar(username, fullname),
                simplecred.INamedUserAvatar,
                lambda: None) # null logout function

DB_DRIVER = "MySQLdb"
DB_ARGS = {
    'db': 'test',
    'user': 'abe',
    'passwd': 'gear42',
    }

if __name__ == "__main__":
    connection = adbapi.ConnectionPool(DB_DRIVER, **DB_ARGS)
    p = portal.Portal(DbRealm(connection))
    p.registerChecker(DbPasswordChecker(connection))
    factory = simplecred.LoginTestFactory(p)
    reactor.listenTCP(2323, factory)
    reactor.run()

