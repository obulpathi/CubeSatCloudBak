#!/usr/bin/env python

import sys
import Queue
import threading
from time import sleep

from twisted.python import log
from twisted.internet import reactor

from cloud.common import *
from cloud.transport.master import *
from cloud.transport.mclient import *
from cloud.transport.server import *
from cloud.transport.gsserver import *
from cloud.transport.gsclient import *
from cloud.transport.worker import *
from cloud.transport.csserver import *
from cloud.transport.csclient import *

class MasterThread(threading.Thread):
    def __init__(self, config):
        self.config = config
        self.fromMasterToMasterClient = Queue.Queue()
        self.fromMasterClientToMaster = Queue.Queue()
        threading.Thread.__init__(self)

    def run(self):
        reactor.connectTCP(config.groundstation.address, config.groundstation.port, 
                        TransportMasterClientFactory(self.fromMasterToMasterClient, self.fromMasterClientToMaster))
        reactor.listenTCP(self.config.port,
                        TransportMasterFactory(self.config.homedir,
                                                self.fromMasterToMasterClient, self.fromMasterClientToMaster))

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
                            TransportWorkerFactory(self.worker.homedir,
                                                    self.fromWorkerToCSClient, self.fromCSClientToWorker,
                                                    self.fromWorkerToCSServer, self.fromCSServerToWorker))
        reactor.connectTCP(self.gsconfig.address, self.gsconfig.port, 
                            TransportCSClientFactory(self.fromWorkerToCSClient, self.fromCSClientToWorker))
        reactor.listenTCP(self.worker.port, 
                            TransportCSServerFactory(self.fromWorkerToCSServer, self.fromCSServerToWorker))

class GroundStationThread(threading.Thread):
    def __init__(self, sconfig, config):
        self.config = config
        self.sconfig = sconfig
        self.fromGSClientToGSServer = Queue.Queue()
        self.fromGSServerToGSClient = Queue.Queue()
        threading.Thread.__init__(self)

    def run(self):
        reactor.connectTCP(self.sconfig.address, self.sconfig.port, 
                            TransportGSClientFactory(self.fromGSClientToGSServer, self.fromGSServerToGSClient))
        reactor.listenTCP(self.config.port, TransportGSServerFactory(self.fromGSClientToGSServer, self.fromGSServerToGSClient))

class ServerThread(threading.Thread):
    def __init__(self, config, commands):
        self.port = config.port
        self.homedir = config.homedir
        self.commands = commands
        threading.Thread.__init__(self)

    def run(self):
        reactor.listenTCP(self.port, TransportServerFactory(self.commands, self.homedir))
        
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
        
    # create and start server
    server = ServerThread(config.server, config.commands)
    server.start()
    sleep(1)
    # create and start master
    master = MasterThread(config.master)
    master.start()
    sleep(1)
    # create and start ground stations
    groundstations = []
    for i in range(NSIZE+1):
        gsconfig = config.groundstation
        gsconfig.port = gsconfig.port + 1
        groundstation = GroundStationThread(config.server, gsconfig)
        groundstation.start()
        groundstations.append(groundstation)
    sleep(1)
    workers = []
    # create and start workers
    for i in range(NSIZE):
        worker = WorkerThread(config.master, config.groundstation, config.worker)
        worker.start()
        workers.append(worker)
    sleep(1)
    # start the reactor
    reactor.run()
    # wait for reactor and all threads to finish
    # end simulation
