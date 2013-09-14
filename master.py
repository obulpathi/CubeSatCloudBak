import sys
import yaml
import Queue

from twisted.python import log
from twisted.internet import reactor

from cloud.common import Struct
from cloud.transport.master import TransportMasterFactory
from cloud.transport.mclient import TransportMasterClientFactory

# run master
if __name__ == "__main__":
    # read the configuration
    f = open('config.yaml')
    configDict = yaml.load(f)
    f.close()
    config = Struct(configDict)
    
    # setup logging
    log.startLogging(sys.stdout)
    
    # setup communication channels
    fromMasterToMasterClient = Queue.Queue()
    fromMasterClientToMaster = Queue.Queue()
    reactor.connectTCP(config.groundstation.address, config.groundstation.port, 
                            TransportMasterClientFactory(fromMasterToMasterClient, fromMasterClientToMaster))
    reactor.listenTCP(config.master.port,
                            TransportMasterFactory(config.master.homedir,
                                                    fromMasterToMasterClient,
                                                    fromMasterClientToMaster))
    reactor.run()
