import sys
import yaml
from multiprocessing import Queue

from twisted.python import log
from twisted.internet import reactor
from twisted.internet import protocol

from cloud.common import *
from cloud.transport.master import *
from cloud.transport.csclient import *

# run master
if __name__ == "__main__":
    # read configuration
    f = open('config.yaml')
    configDict = yaml.load(f)
    f.close()
    config = Struct(configDict)
    # set up logging
    #log.startLogging(open('/var/log/master.log', 'w'))
    log.startLogging(sys.stdout)
    reactor.connectTCP(config.groundstation.address, config.groundstation.port, 
                            TransportMasterClientFactory(fromMasterToMasterClient, fromMasterClientToMaster))
    reactor.listenTCP(config.master.port, TransportMasterFactory())
    reactor.run()
