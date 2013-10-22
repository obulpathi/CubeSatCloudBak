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

class MasterThread(threading.Thread):
    def __init__(self, config, fromMasterToMasterClient, fromMasterClientToMaster):
        self.config = config.master
        self.sconfig = config.server
        self.fromMasterToMasterClient = fromMasterToMasterClient
        self.fromMasterClientToMaster = fromMasterClientToMaster
        threading.Thread.__init__(self)
    def run(self):
        log.msg("running master factory thread")
        reactor.listenTCP(self.config.port,
                        TransportMasterFactory(self.config.homedir,
                                                self.fromMasterToMasterClient, self.fromMasterClientToMaster))
                                                    
class MasterClientThread(threading.Thread):
    def __init__(self, config, fromMasterToMasterClient, fromMasterClientToMaster):
        self.config = config.master
        self.sconfig = config.server
        self.fromMasterToMasterClient = fromMasterToMasterClient
        self.fromMasterClientToMaster = fromMasterClientToMaster
        threading.Thread.__init__(self)        
    def run(self):
        log.msg("running master client factory thread ############################")
        reactor.connectTCP(self.sconfig.address, self.sconfig.ssport, 
                        TransportMasterClientFactory(self.fromMasterToMasterClient, self.fromMasterClientToMaster))

"""
class MasterThread(threading.Thread):
    def __init__(self, config):
        self.config = config.master
        self.sconfig = config.server
        self.fromMasterToMasterClient = Queue.Queue()
        self.fromMasterClientToMaster = Queue.Queue()
        threading.Thread.__init__(self)

    def run(self):
        reactor.listenTCP(self.config.port,
                        TransportMasterFactory(self.config.homedir,
                                                self.fromMasterToMasterClient, self.fromMasterClientToMaster))
        reactor.connectTCP(self.sconfig.address, self.sconfig.ssport, 
                        TransportMasterClientFactory(self.fromMasterToMasterClient, self.fromMasterClientToMaster))
"""
        
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
    
    # create interprocessing queues
    fromMasterToMasterClient = Queue.Queue()
    fromMasterClientToMaster = Queue.Queue()
    
    # create and start master
    #masterThread = MasterThread(config, fromMasterToMasterClient, fromMasterClientToMaster)
    #masterThread.start()
    #masterClientThread = MasterClientThread(config, fromMasterToMasterClient, fromMasterClientToMaster)
    #masterClientThread.start()
    reactor.connectTCP(config.server.address, config.server.ssport, 
                        TransportMasterClientFactory(fromMasterToMasterClient, fromMasterClientToMaster))
    reactor.listenTCP(config.master.port,
                        TransportMasterFactory(config.master.homedir,
                                                fromMasterToMasterClient, fromMasterClientToMaster))
    reactor.run()
    print("##############################")
    # wait for reactor and all threads to finish
    # end simulation
