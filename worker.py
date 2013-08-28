from twisted.python import log
from twisted.internet import reactor
from twisted.internet import protocol

import sys
import yaml
from multiprocessing import Queue

from cloud.common import *
from cloud.transport.worker import *
from cloud.transport.csclient import *
from cloud.transport.csserver import *

# run the worker and twisted reactor
if __name__ == "__main__":
    # read configuration
    f = open('config.yaml')
    configDict = yaml.load(f)
    f.close()
    config = Struct(configDict)
    # set up logging
    #log.startLogging(open('/var/log/master.log', 'w'))
    log.startLogging(sys.stdout)
    #set up IPC channels
    fromWorkerToCSClient = Queue()
    fromCSClientToWorker = Queue()
    fromWorkerToCSServer = Queue()
    fromCSServerToWorker = Queue()
    
    # start Worker, CSClient and CSServer
    reactor.connectTCP(config.master.address, config.master.port,
                        TransportWorkerFactory(fromWorkerToCSClient, fromCSClientToWorker,
                                               fromWorkerToCSServer, fromCSServerToWorker))
    reactor.connectTCP(config.groundstation.address, config.groundstation.port, 
                        TransportCSClientFactory(fromWorkerToCSClient, fromCSClientToWorker))
    reactor.listenTCP(config.csserver.port,
                        TransportCSServerFactory(fromWorkerToCSServer, fromCSServerToWorker))
    reactor.run()
