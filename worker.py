#!/usr/bin/env python

import sys
import copy
import Queue
import threading
from time import sleep

from twisted.python import log
from twisted.internet import reactor

from cloud.common import *
from cloud.transport.master import *
from cloud.transport.mclient import *
from cloud.transport.server import *
from cloud.transport.sserver import *
from cloud.transport.gsserver import *
from cloud.transport.gsclient import *
from cloud.transport.worker import *
from cloud.transport.csserver import *
from cloud.transport.csclient import *

class WorkerThread(threading.Thread):
    def __init__(self, mconfig, gsconfig, worker):
        self.mconfig  = mconfig
        self.gsconfig = gsconfig
        self.worker = worker
        self.fromWorkerToCSClient = Queue.Queue()
        self.fromCSClientToWorker = Queue.Queue()
        self.fromWorkerToCSServer = Queue.Queue()
        self.fromCSServerToWorker = Queue.Queue()
        threading.Thread.__init__(self)

    def run(self):
        reactor.connectTCP(self.mconfig.address, self.mconfig.port,
                            TransportWorkerFactory(self.worker.address, self.worker.homedir,
                                                    self.fromWorkerToCSClient, self.fromCSClientToWorker,
                                                    self.fromWorkerToCSServer, self.fromCSServerToWorker))
        reactor.connectTCP(self.gsconfig.address, self.gsconfig.port, 
                            TransportCSClientFactory(self.fromWorkerToCSClient, self.fromCSClientToWorker))
        reactor.listenTCP(self.worker.port, 
                            TransportCSServerFactory(self.fromWorkerToCSServer, self.fromCSServerToWorker))

        
if __name__ == "__main__":
    import yaml
    from cloud.common import Struct

    # read the configuration
    f = open('config.yaml')
    configDict = yaml.load(f)
    f.close()
    config = Struct(configDict)
    
    # setup logging
    log.startLogging(sys.stdout)
    
    # set network size
    if len(sys.argv) > 1:
        NSIZE = int(sys.argv[1])
    else:
        NSIZE = 1
    
    """    
    # create and start server
    server = ServerThread(config.server, config.commands)
    server.start()
    sleep(1)
    # create and start ground stations
    groundstations = []
    for i in range(NSIZE):
        gsconfig = copy.deepcopy(config.groundstation)
        gsconfig.port = gsconfig.port + i
        print(gsconfig)
        groundstation = GroundStationThread(config.server, gsconfig)
        groundstation.start()
        groundstations.append(groundstation)
    sleep(1)
    # create and start master
    master = MasterThread(config)
    master.start()
    sleep(1)
    """
    workers = []
    # create and start workers
    for i in range(NSIZE):
        wconfig = copy.deepcopy(config.worker)
        wconfig.address = i
        wconfig.port = wconfig.port + i
        gsconfig = copy.deepcopy(config.groundstation)
        gsconfig.port = gsconfig.port + i
        worker = WorkerThread(config.master, gsconfig, wconfig)
        worker.start()
        workers.append(worker)
    sleep(1)
    # start the reactor
    reactor.run()
    # wait for reactor and all threads to finish
    # end simulation
