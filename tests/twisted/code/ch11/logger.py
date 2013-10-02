from twisted.internet import protocol
from twisted.protocols import basic
from twisted.application import service, internet
from twisted.python import log, logfile
import time

class ChatProtocol(basic.LineReceiver):
    def lineReceived(self, line):
        log.msg("Got command:", line)
        
        parts = line.split()
        cmd = parts[0]
        args = parts[1:]

        if hasattr(self, 'do_'+cmd):
            try:
                getattr(self, 'do_'+cmd)(*args)
            except Exception, e:
                log.err(e)
                self.sendLine("Error: %s" % e)
        else:
            log.msg("User sent invalid command", cmd, args)
            self.sendLine("Invalid command '%s'" % cmd)

    def do_time(self):
        self.sendLine(str(time.strftime("%x %X")))

    def do_echo(self, *strings):
        self.sendLine(" ".join(strings))

    def do_quit(self):
        self.transport.loseConnection()

class ErrorLog(log.FileLogObserver):
    def emit(self, logEntryDict):
        if not logEntryDict.get('isError'): return
        log.FileLogObserver.emit(self, logEntryDict)

class ErrLogService(service.Service):
    def __init__(self, logName, logDir):
        self.logName = logName
        self.logDir = logDir
        self.maxLogSize = 1000000
    
    def startService(self):
        # logfile is a file-like object that supports rotation
        self.logFile = logfile.LogFile(
            self.logName, self.logDir, rotateLength=self.maxLogSize)
        self.logFile.rotate() # force rotation each time restarted
        self.errlog = ErrorLog(self.logFile)
        self.errlog.start()

    def stopService(self):
        self.errlog.stop()
        self.logFile.close()
        del(self.logFile)

application = service.Application("LogDemo")

# quick and dirty way to create a service from a protocol
chatFactory = protocol.ServerFactory()
chatFactory.protocol = ChatProtocol
chatService = internet.TCPServer(2323, chatFactory)
chatService.setServiceParent(application)

ERR_LOG_DIR = "." # use an absolute path for real apps
ERR_LOG_NAME = "chaterrors.log"

ErrLogService(ERR_LOG_NAME, ERR_LOG_DIR).setServiceParent(application)
