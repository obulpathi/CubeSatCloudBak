from sshserver import SSHDemoRealm, getRSAKeys
from twisted.conch import credentials, error
from twisted.conch.ssh import keys, factory
from twisted.cred import checkers, portal
from twisted.python import failure
from zope.interface import implements
import base64

class PublicKeyCredentialsChecker:
    implements(checkers.ICredentialsChecker)
    credentialInterfaces = (credentials.ISSHPrivateKey,)
    
    def __init__(self, authorizedKeys):
        self.authorizedKeys = authorizedKeys
        
    def requestAvatarId(self, credentials):
        if self.authorizedKeys.has_key(credentials.username):
            userKey = self.authorizedKeys[credentials.username]
            if not credentials.blob == base64.decodestring(userKey):
                raise failure.failure(
                    error.ConchError("I don't recognize that key"))
            if not credentials.signature:
                return failure.Failure(error.ValidPublicKey())
            pubKey = keys.getPublicKeyObject(data=credentials.blob)
            if keys.verifySignature(pubKey, credentials.signature,
                                    credentials.sigData):
                return credentials.username
            else:
                return failure.Failure(
                    error.ConchError("Incorrect signature"))
        else:
            return failure.Failure(error.ConchError("No such user"))
            
if __name__ == "__main__":
    sshFactory = factory.SSHFactory()
    sshFactory.portal = portal.Portal(SSHDemoRealm())
    authorizedKeys = {
    "admin": "AAAAB3NzaC1yc2EAAAABIwAAAIEAyr5G+E+alVigip1T1zsb4hdSICcpNfnslpDerRO9cGQoatku25A8hfu5Agc32L9hubOELmTPNmDAocRh8U2xNzRvFL+8qdESIuyeCweZBFjRrAmBcZ+0fHK5YrCIzq1WDLlyQ1GIst4o5gk0yhtPdilNyKJKFTBAXWQSLy99ga8="
    }
    sshFactory.portal.registerChecker(
        PublicKeyCredentialsChecker(authorizedKeys))
     
    pubKeyString, privKeyString = getRSAKeys()
    sshFactory.publicKeys = {
        'ssh-rsa': keys.getPublicKeyString(data=pubKeyString)}
    sshFactory.privateKeys = {
        'ssh-rsa': keys.getPrivateKeyObject(data=privKeyString)}

    from twisted.internet import reactor
    reactor.listenTCP(2222, sshFactory)
    reactor.run()
