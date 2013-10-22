#!/usr/bin/env python

import sys
import copy
import Queue
import threading
from time import sleep

from twisted.python import log
from twisted.internet import reactor

from cloud.common import *
from cloud.transport.server import *
from cloud.transport.sserver import *
from cloud.transport.gsserver import *
from cloud.transport.gsclient import *

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
        print(self.config.port)
        reactor.listenTCP(self.config.port, TransportGSServerFactory(self.fromGSClientToGSServer, self.fromGSServerToGSClient))

class ServerThread(threading.Thread):
    def __init__(self, config, commands):
        self.port = config.port
        self.ssport = config.ssport
        self.homedir = config.homedir
        self.commands = commands
        self.fromSServerToServer = Queue.Queue()
        self.fromServerToSServer = Queue.Queue()
        threading.Thread.__init__(self)

    def run(self):
        reactor.listenTCP(self.ssport, 
                            TransportSServerFactory(self.fromSServerToServer, self.fromServerToSServer))
        reactor.listenTCP(self.port, 
                            TransportServerFactory(self.commands, self.homedir, 
                                                    self.fromSServerToServer, self.fromServerToSServer))

        
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
    # server = ServerThread(config.server, config.commands)
    # server.start()
    fromSServerToServer = Queue.Queue()
    fromServerToSServer = Queue.Queue()
    reactor.listenTCP(config.server.ssport, 
                        TransportSServerFactory(fromSServerToServer, fromServerToSServer))
    reactor.listenTCP(config.server.port, 
                        TransportServerFactory(config.commands, config.server.homedir, 
                                                fromSServerToServer, fromServerToSServer))    
    """
    # create and start ground stations
    groundstations = []
    for i in range(NSIZE):
        gsconfig = copy.deepcopy(config.groundstation)
        gsconfig.port = gsconfig.port + i
        print(gsconfig)
        groundstation = GroundStationThread(config.server, gsconfig)
        groundstation.start()
        groundstations.append(groundstation)
    """
    # start the reactor
    reactor.run()
    # wait for reactor and all threads to finish
