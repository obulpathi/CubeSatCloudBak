from twisted.python import log
from twisted.internet import reactor
from twisted.internet import protocol

import sys
from multiprocessing import Queue

from cloud.common import *
from cloud.transport.csclient import *
from cloud.transport.csserver import *

# run the worker and twisted reactor
if __name__ == "__main__":
    # set up logging
    #log.startLogging(open('/var/log/master.log', 'w'))
    log.startLogging(sys.stdout)
    #set up IPC channels
    fromCSServerToCSCleint = Queue()
    fromCSClientToCSServer = Queue()
    
    # start client and router
    reactor.connectTCP("localhost", 8000, TransportCSClientFactory(None, fromCSClientToCSServer, fromCSServerToCSCleint))
    reactor.listenTCP(8008, TransportCSServerFactory(fromCSClientToCSServer, fromCSServerToCSCleint))
    log.msg("CSClient and CSServer are up and running")
    reactor.run()
