#!/usr/bin/env python

import sys
import threading
from time import sleep
from multiprocessing import Queue

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
        self.fromMasterToMasterClient = Queue()
        self.fromMasterClientToMaster = Queue()
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
        self.fromWorkerToCSClient = Queue()
        self.fromCSClientToWorker = Queue()
        self.fromWorkerToCSServer = Queue()
        self.fromCSServerToWorker = Queue()
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
        self.fromGSClientToGSServer = Queue()
        self.fromGSServerToGSClient = Queue()
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
    
    # create and start server
    server = ServerThread(config.server, config.commands)
    server.start()
    sleep(1)
    # create and start master
    master = MasterThread(config.master)
    master.start()
    sleep(1)
    # create and start ground station
    groundstation = GroundStationThread(config.server, config.groundstation)
    groundstation.start()
    sleep(1)
    # create and start ground stations
    gs0 = GroundStationThread(config.server, config.groundstation0)
    #gs1 = GroundStationThread(config.server, config.groundstation1)
    #gs2 = GroundStationThread(config.server, config.groundstation2)
    gs0.start()
    #gs1.start()
    #gs2.start()
    sleep(1)
    # create worker threads: mconfig, gsconfig, worker
    worker0 = WorkerThread(config.master, config.groundstation0, config.worker0)
    #worker1 = WorkerThread(config.master, config.groundstation1, config.worker1)
    #worker2 = WorkerThread(config.master, config.groundstation2, config.worker2)
    # create ground station threads
    worker0.start()
    #worker1.start()
    #worker2.start()
    sleep(1)
    # start the reactor
    reactor.run()
    # wait for reactor and all threads to finish
    # end simulation
