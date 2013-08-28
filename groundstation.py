import sys
import yaml
from multiprocessing import Queue

from twisted.python import log
from twisted.internet import reactor
from twisted.internet import protocol

from cloud.common import *
from cloud.transport.gsclient import *
from cloud.transport.gsserver import *

# run the worker and twisted reactor
if __name__ == "__main__":
    # read configuration
    f = open('config.yaml')
    configDict = yaml.load(f)
    f.close()
    config = Struct(configDict)
    # setup logging
    #log.startLogging(open('/var/log/groundstation.log', 'w'))
    log.startLogging(sys.stdout)
    fromGSClientToGSServer = Queue()
    fromGSServerToGSClient = Queue()
    # start GSClient and GSServer
    reactor.connectTCP(config.server.address, config.server.port, 
                        TransportGSClientFactory(fromGSClientToGSServer, fromGSServerToGSClient))
    reactor.listenTCP(config.groundstation.port, 
                        TransportGSServerFactory(fromGSClientToGSServer, fromGSServerToGSClient))
    log.msg("GSClient and GSServer are up and running")
    reactor.run()
