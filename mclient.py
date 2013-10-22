#!/usr/bin/env python

import sys
import copy
import Queue
import threading
from time import sleep

from twisted.python import log
from twisted.internet import reactor

from cloud.common import *
from cloud.transport.mclient import *

class MasterThread(threading.Thread):
    def __init__(self, config):
        self.config = config.master
        self.sconfig = config.server
        self.fromMasterToMasterClient = Queue.Queue()
        self.fromMasterClientToMaster = Queue.Queue()
        threading.Thread.__init__(self)

    def run(self):
        reactor.connectTCP(self.sconfig.address, self.sconfig.ssport,
                        TransportMasterClientFactory(self.fromMasterToMasterClient, self.fromMasterClientToMaster))
        
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
    
    # create and start master
    # master = MasterThread(config)
    # master.start()
    fromMasterToMasterClient = Queue.Queue()
    fromMasterClientToMaster = Queue.Queue()
    reactor.connectTCP(config.server.address, config.server.ssport, 
                        TransportMasterClientFactory(fromMasterToMasterClient, fromMasterClientToMaster))
    # start the reactor
    reactor.run()
    # wait for reactor and all threads to finish
    # end simulation
