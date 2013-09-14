import sys
import yaml
import Queue

from twisted.python import log
from twisted.internet import reactor

from cloud.common import Struct
from cloud.transport.worker import TransportWorkerFactory
from cloud.transport.csclient import TransportCSClientFactory
from cloud.transport.csserver import TransportCSServerFactory

# run the worker and twisted reactor
if __name__ == "__main__":
    # read the configuration
    f = open('config.yaml')
    configDict = yaml.load(f)
    f.close()
    config = Struct(configDict)
    
    # setup logging
    log.startLogging(sys.stdout)
    
    #set up IPC channels
    fromWorkerToCSClient = Queue.Queue()
    fromCSClientToWorker = Queue.Queue()
    fromWorkerToCSServer = Queue.Queue()
    fromCSServerToWorker = Queue.Queue()
    
    # configure
    worker = config.worker
    groundstation = config.groundstation
    if len(sys.argv) > 1:
        worker.port = worker.port + int(sys.argv[1])
        groundstation.port = groundstation.port + int(sys.argv[1])
        worker.homedir = worker.homedir + sys.argv[1]
    
    # start Worker, CSClient and CSServer
    reactor.connectTCP(config.master.address, config.master.port,
                        TransportWorkerFactory(sys.argv[1], worker.homedir,
                                                fromWorkerToCSClient, fromCSClientToWorker,
                                                fromWorkerToCSServer, fromCSServerToWorker))
    reactor.connectTCP(groundstation.address, groundstation.port, 
                        TransportCSClientFactory(fromWorkerToCSClient, fromCSClientToWorker))
    reactor.listenTCP(worker.port,
                        TransportCSServerFactory(fromWorkerToCSServer, fromCSServerToWorker))
    reactor.run()
