import sys
import yaml
import Queue

from twisted.python import log
from twisted.internet import reactor
from twisted.internet import protocol

from cloud.common import Struct
from cloud.transport.gsclient import TransportGSClientFactory
from cloud.transport.gsserver import TransportGSServerFactory

# run the worker and twisted reactor
if __name__ == "__main__":
    # read the configuration
    f = open('config.yaml')
    configDict = yaml.load(f)
    f.close()
    config = Struct(configDict)
    
    # setup logging
    log.startLogging(sys.stdout)
    
    # create communication channels
    fromGSClientToGSServer = Queue.Queue()
    fromGSServerToGSClient = Queue.Queue()
    
    # configure
    worker = config.worker
    groundstation = config.groundstation
    if len(sys.argv) > 1:
        groundstation.port = groundstation.port + int(sys.argv[1])
    
    # start GSClient and GSServer
    while True:
        reactor.connectTCP(config.server.address, config.server.port, 
                            TransportGSClientFactory(fromGSClientToGSServer, fromGSServerToGSClient))
        reactor.listenTCP(groundstation.port,
                            TransportGSServerFactory(fromGSClientToGSServer, fromGSServerToGSClient))
        log.msg("GSClient and GSServer are up and running")
        reactor.run()
