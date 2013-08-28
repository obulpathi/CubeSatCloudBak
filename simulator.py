#!/usr/bin/env python

import sys
import threading
from multiprocessing import Queue

from twisted.python import log
from twisted.internet import reactor

from cloud.common import *
from cloud.transport.master import *
from cloud.transport.server import *
from cloud.transport.gsserver import *
from cloud.transport.gsclient import *
from cloud.transport.worker import *
from cloud.transport.csserver import *
from cloud.transport.csclient import *

class MasterThread(threading.Thread):
    def __init__(self, config):
        self.config = config
        threading.Thread.__init__(self)
    def run(self):
        reactor.listenTCP(self.config.port, TransportMasterFactory())

class WorkerThread(threading.Thread):
    def __init__(self, mconfig, gsconfig, csconfig):
        self.mconfig  = mconfig
        self.gsconfig = gsconfig
        self.csconfig = csconfig
        self.fromWorkerToCSClient = Queue()
        self.fromCSClientToWorker = Queue()
        self.fromWorkerToCSServer = Queue()
        self.fromCSServerToWorker = Queue()
        threading.Thread.__init__(self)
    def run(self):
        reactor.connectTCP(self.mconfig.address, self.mconfig.port,
                            TransportWorkerFactory(self.fromWorkerToCSClient, self.fromCSClientToWorker,
                                                   self.fromWorkerToCSServer, self.fromCSServerToWorker))
        reactor.connectTCP(self.gsconfig.address, self.gsconfig.address, 
                            TransportCSClientFactory(self.fromWorkerToCSClient, self.fromCSClientToWorker))
        reactor.listenTCP(self.csconfig.port, 
                            TransportCSServerFactory(self.fromWorkerToCSServer, self.fromCSServerToWorker))

class GroundStationThread(threading.Thread):
    def __init__(self, config, sconfig):
        self.config = config
        self.sconfig = sconfig
        self.fromGSClientToGSServer = Queue()
        self.fromGSServerToGSClient = Queue()
        threading.Thread.__init__(self)
    def run(self):
        reactor.connectTCP(self.sconfig.address, self.sconfig.port, 
                            TransportGSClientFactory(self.fromGSClientToGSServer, self.fromGSServerToGSClient))
        reactor.listenTCP(self.config.port, TransportGSServerFactory(self.fromGSClientToGSServer, self.fromGSServerToGSClient))

class ServerThread(threading.Thread):
    def __init__(self, config):
        self.port = config.port
        threading.Thread.__init__(self)
    def run(self):
        reactor.listenTCP(self.port, TransportServerFactory())
        
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
    
    # create simulator objects
    # create master thread
    master = MasterThread(config.master)
    # create worker threads: mconfig, gsconfig, csconfig
    worker0 = WorkerThread(config.master, config.groundstation0, config.worker0)
    #worker1 = WorkerThread(config.master, config.groundstation1, config.worker1)
    #worker2 = WorkerThread(config.master, config.groundstation2, config.worker2)
    # create ground station threads
    gs0 = GroundStationThread(config.server, config.groundstation0)
    #gs1 = GroundStationThread(config.server, config.groundstation1)
    #gs2 = GroundStationThread(config.server, config.groundstation2)
    # create server thread
    server = ServerThread(config.server)
    # start the components
    server.start()
    gs0.start()
    #gs1.start()
    #gs2.start()
    master.start()
    worker0.start()
    #worker1.start()
    #worker2.start()
    # start the reactor
    reactor.run()
    # wait for all threads to finish
    # end simulation
