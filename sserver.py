#!/usr/bin/env python

import sys
import copy
import Queue
import threading
from time import sleep

from twisted.python import log
from twisted.internet import reactor

from cloud.common import *
from cloud.transport.sserver import *

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
    reactor.listenTCP(config.server.ssport, TransportSServerFactory(fromSServerToServer, fromServerToSServer))
    # start the reactor
    reactor.run()
    # wait for reactor and all threads to finish
    # end simulation
