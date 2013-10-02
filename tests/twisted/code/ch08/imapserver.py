from twisted.mail import imap4, maildir
from twisted.internet import reactor, defer, protocol
from twisted.cred import portal, checkers, credentials
from twisted.cred import error as credError
from twisted.python import filepath
from zope.interface import implements
import time, os, random, pickle

MAILBOXDELIMITER = "."
    
class IMAPUserAccount(object):
    implements(imap4.IAccount)

    def __init__(self, userDir):
        self.dir = userDir
        self.mailboxCache = {}
        # make sure Inbox exists
        inbox = self._getMailbox("Inbox", create=True)
            
    def listMailboxes(self, ref, wildcard):
        for box in os.listdir(self.dir):
            yield box, self._getMailbox(box)

    def select(self, path, rw=True):
        "return an object implementing IMailbox for the given path"
        return self._getMailbox(path)

    def _getMailbox(self, path, create=False):
        """
        Helper function to get a mailbox object at the given
        path, optionally creating it if it doesn't already exist.
        """
        # According to the IMAP spec, Inbox is case-insensitive
        pathParts = path.split(MAILBOXDELIMITER)
        if pathParts[0].lower() == 'inbox': pathParts[0] = 'Inbox'
        path = MAILBOXDELIMITER.join(pathParts)
        
        if not self.mailboxCache.has_key(path):
            fullPath = os.path.join(self.dir, path)
            if not os.path.exists(fullPath):
                if create:
                    maildir.initializeMaildir(fullPath)
                else:
                    raise KeyError, "No such mailbox"
            self.mailboxCache[path] = IMAPMailbox(fullPath)
        return self.mailboxCache[path]
        
    def create(self, path):
        "create a mailbox at path and return it"
        self._getMailbox(path, create=True)

    def delete(self, path):
        "delete the mailbox at path"
        raise imap4.MailboxException("Permission denied.")

    def rename(self, oldname, newname):
        "rename a mailbox"
        oldPath = os.path.join(self.dir, oldname)
        newPath = os.path.join(self.dir, newname)
        os.rename(oldPath, newPath)
    
    def isSubscribed(self, path):
        "return a true value if user is subscribed to the mailbox"
        return self._getMailbox(path).metadata.get('subscribed', False)
        
    def subscribe(self, path):
        "mark a mailbox as subscribed"
        box = self._getMailbox(path)
        box.metadata['subscribed'] = True
        box.saveMetadata()
        return True
        
    def unsubscribe(self, path):
        "mark a mailbox as unsubscribed"
        box = self._getMailbox(path)
        box.metadata['subscribed'] = False
        box.saveMetadata()
        return True

class ExtendedMaildir(maildir.MaildirMailbox):
    """
    Extends maildir.MaildirMailbox to expose more
    of the underlying filename data
    """
    def __iter__(self):
        "iterates through the full paths of all messages in the maildir"
        return iter(self.list)

    def __len__(self):
        return len(self.list)

    def __getitem__(self, i):
        return self.list[i]

    def deleteMessage(self, filename):
        index = self.list.index(filename)
        os.remove(filename)
        del(self.list[index])
    
class IMAPMailbox(object):
    implements(imap4.IMailbox)

    def __init__(self, path):
        self.maildir = ExtendedMaildir(path)
        self.metadataFile = os.path.join(path, '.imap-metadata.pickle')
        if os.path.exists(self.metadataFile):
            self.metadata = pickle.load(file(self.metadataFile, 'r+b'))
        else:
            self.metadata = {}
        self.initMetadata()
        self.listeners = []
        self._assignUIDs()

    def initMetadata(self):
        if not self.metadata.has_key('flags'):
            self.metadata['flags'] = {} # dict of message IDs to flags
        if not self.metadata.has_key('uidvalidity'):
            # create a unique integer ID to identify this version of
            # the mailbox, so the client could tell if it was deleted
            # and replaced by a different mailbox with the same name
            self.metadata['uidvalidity'] = random.randint(1000000, 9999999)
        if not self.metadata.has_key('uids'):
            self.metadata['uids'] = {}
        if not self.metadata.has_key('uidnext'):
            self.metadata['uidnext'] = 1 # next UID to be assigned

    def saveMetadata(self):
        pickle.dump(self.metadata, file(self.metadataFile, 'w+b'))

    def _assignUIDs(self):
        # make sure every message has a uid
        for messagePath in self.maildir:
            messageFile = os.path.basename(messagePath)
            if not self.metadata['uids'].has_key(messageFile):
                self.metadata['uids'][messageFile] = self.metadata['uidnext']
                self.metadata['uidnext'] += 1
        self.saveMetadata()

    def getHierarchicalDelimiter(self):
        return MAILBOXDELIMITER
    
    def getFlags(self):
        "return list of flags supported by this mailbox"
        return [r'\Seen', r'\Unseen', r'\Deleted',
                r'\Flagged', r'\Answered', r'\Recent']
        
    def getMessageCount(self):
        return len(self.maildir)

    def getRecentCount(self):
        return 0

    def getUnseenCount(self):
        def messageIsUnseen(filename):
            filename = os.path.basename(filename)
            uid = self.metadata['uids'].get(filename)
            flags = self.metadata['flags'].get(uid, [])
            if not r'\Seen' in flags:
                return True
        return len(filter(messageIsUnseen, self.maildir))

    def isWriteable(self):
        return True

    def getUIDValidity(self):
        return self.metadata['uidvalidity']
        
    def getUID(self, messageNum):
        filename = os.path.basename(self.maildir[messageNum-1])
        return self.metadata['uids'][filename]
        
    def getUIDNext(self):
        return self.folder.metadata['uidnext']
                
    def _uidMessageSetToSeqDict(self, messageSet):
        """
        take a MessageSet object containing UIDs, and return
        a dictionary mapping sequence numbers to filenames
        """
        # if messageSet.last is None, it means 'the end', and needs to
        # be set to a sane high number before attempting to iterate
        # through the MessageSet
        if not messageSet.last:
            messageSet.last = self.metadata['uidnext']
        allUIDs = []
        for filename in self.maildir:
            shortFilename = os.path.basename(filename)
            allUIDs.append(self.metadata['uids'][shortFilename])
        allUIDs.sort()
        seqMap = {}
        for uid in messageSet:
            # the message set covers a span of UIDs. not all of them
            # will necessarily exist, so check each one for validity
            if uid in allUIDs:
                sequence = allUIDs.index(uid)+1
                seqMap[sequence] = self.maildir[sequence-1]
        return seqMap

    def _seqMessageSetToSeqDict(self, messageSet):
        """
        take a MessageSet object containing message sequence numbers,
        and return a dictionary mapping sequence number to filenames
        """
        # if messageSet.last is None, it means 'the end', and needs to
        # be set to a sane high number before attempting to iterate
        # through the MessageSet
        if not messageSet.last: messageSet.last = len(self.maildir)-1
        seqMap = {}
        for messageNo in messageSet:
            seqMap[messageNo] = self.maildir[messageNo-1]
        return seqMap

    def fetch(self, messages, uid):
        if uid:
            messagesToFetch = self._uidMessageSetToSeqDict(messages)
        else:
            messagesToFetch = self._seqMessageSetToSeqDict(messages)
        for seq, filename in messagesToFetch.items():
            uid = self.getUID(seq)
            flags = self.metadata['flags'].get(uid, [])
            yield seq, MaildirMessage(file(filename).read(), uid, flags)
            
    def addListener(self, listener):
        self.listeners.append(listener)
        return True
    
    def removeListener(self, listener):
        self.listeners.remove(listener)
        return True
        
    def requestStatus(self, path):
        return imap4.statusRequestHelper(self, path)
    
    def addMessage(self, msg, flags=None, date=None):
        if flags is None: flags = []
        return self.maildir.appendMessage(msg).addCallback(
            self._addedMessage, flags)

    def _addedMessage(self, _, flags):
        # the first argument is the value returned from
        # MaildirMailbox.appendMessage. It doesn't contain any meaningful
        # information and can be discarded. Using the name "_" is a Twisted
        # idiom for unimportant return values.
        self._assignUIDs()
        messageFile = os.path.basename(self.maildir[-1])
        messageID = self.metadata['uids'][messageFile]
        self.metadata['flags'][messageID] = flags
        self.saveMetadata()

    def store(self, messageSet, flags, mode, uid):
        if uid:
            messages = self._uidMessageSetToSeqDict(messageSet)
        else:
            messages = self._seqMessageSetToSeqDict(messageSet)
        setFlags = {}
        for seq, filename in messages.items():
            uid = self.getUID(seq)
            if mode == 0: # replace flags
                messageFlags = self.metadata['flags'][uid] = flags
            else:
                messageFlags = self.metadata['flags'].setdefault(uid, [])
                for flag in flags:
                    # mode 1 is append, mode -1 is delete
                    if mode == 1 and not messageFlags.count(flag):
                        messageFlags.append(flag)
                    elif mode == -1 and messageFlags.count(flag):
                        messageFlags.remove(flag)
            setFlags[seq] = messageFlags
        self.saveMetadata()
        return setFlags

    def expunge(self):
        "remove all messages marked for deletion"
        removed = []
        for filename in self.maildir:
            uid = self.metadata['uids'].get(os.path.basename(filename))
            if r"\Deleted" in self.metadata['flags'].get(uid, []):
                self.maildir.deleteMessage(filename)
                # you could also throw away the metadata here
                removed.append(uid)
        return removed

    def destroy(self):
        "complete remove the mailbox and all its contents"
        raise imap4.MailboxException("Permission denied.")

from cStringIO import StringIO
import email

class MaildirMessagePart(object):
    implements(imap4.IMessagePart)

    def __init__(self, mimeMessage):
        self.message = mimeMessage
        self.data = str(self.message)

    def getHeaders(self, negate, *names):
        """
        Return a dict mapping header name to header value. If *names
        is empty, match all headers; if negate is true, return only
        headers _not_ listed in *names.
        """
        if not names: names = self.message.keys()
        headers = {}
        if negate:
            for header in self.message.keys():
                if header.upper() not in names:
                    headers[header.lower()] = self.message.get(header, '')
        else:
            for name in names:
                headers[name.lower()] = self.message.get(name, '')
        return headers

    def getBodyFile(self):
        "return a file-like object containing this message's body"
        bodyData = str(self.message.get_payload())
        return StringIO(bodyData)

    def getSize(self):
        return len(self.data)

    def getInternalDate(self):
        return self.message.get('Date', '')

    def isMultipart(self):
        return self.message.is_multipart()

    def getSubPart(self, partNo):
        return MaildirMessagePart(self.message.get_payload(partNo))
    
class MaildirMessage(MaildirMessagePart):
    implements(imap4.IMessage)

    def __init__(self, messageData, uid, flags):
        self.data = messageData
        self.message = email.message_from_string(self.data)
        self.uid = uid
        self.flags = flags

    def getUID(self):
        return self.uid

    def getFlags(self):
        return self.flags

class MailUserRealm(object):
    implements(portal.IRealm)
    avatarInterfaces = {
        imap4.IAccount: IMAPUserAccount,
        }

    def __init__(self, baseDir):
        self.baseDir = baseDir

    def requestAvatar(self, avatarId, mind, *interfaces):
        for requestedInterface in interfaces:
            if self.avatarInterfaces.has_key(requestedInterface):
                # make sure the user dir exists (avatarId is username)
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

def passwordFileToDict(filename):
    passwords = {}
    for line in file(filename):
        if line and line.count(':'):
            username, password = line.strip().split(':')
            passwords[username] = password
    return passwords
    
class CredentialsChecker(object):
    implements(checkers.ICredentialsChecker)
    credentialInterfaces = (credentials.IUsernamePassword,
                            credentials.IUsernameHashedPassword)

    def __init__(self, passwords):
        "passwords: a dict-like object mapping usernames to passwords"
        self.passwords = passwords

    def requestAvatarId(self, credentials):
        """
        check to see if the supplied credentials authenticate.
        if so, return an 'avatar id', in this case the name of
        the IMAP user.
        The supplied credentials will implement one of the classes
        in self.credentialInterfaces. In this case both
        IUsernamePassword and IUsernameHashedPassword have a
        checkPassword method that takes the real password and checks
        it against the supplied password.
        """
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

class IMAPServerProtocol(imap4.IMAP4Server):
    "Subclass of imap4.IMAP4Server that adds debugging."
    debug = True

    def lineReceived(self, line):
        if self.debug:
            print "CLIENT:", line
        imap4.IMAP4Server.lineReceived(self, line)
        
    def sendLine(self, line):
        imap4.IMAP4Server.sendLine(self, line)
        if self.debug:
            print "SERVER:", line

class IMAPFactory(protocol.Factory):
    protocol = IMAPServerProtocol
    portal = None # placeholder
    
    def buildProtocol(self, address):
        p = self.protocol()
        p.portal = self.portal
        p.factory = self
        return p
    
if __name__ == "__main__":
    import sys
    dataDir = sys.argv[1]
    
    portal = portal.Portal(MailUserRealm(dataDir))
    passwordFile = os.path.join(dataDir, 'passwords.txt')
    passwords = passwordFileToDict(passwordFile)
    passwordChecker = CredentialsChecker(passwords)
    portal.registerChecker(passwordChecker)

    factory = IMAPFactory()
    factory.portal = portal
    
    reactor.listenTCP(143, factory)
    reactor.run()
