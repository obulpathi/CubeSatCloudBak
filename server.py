import sys
import yaml

from twisted.python import log
from twisted.internet import reactor

from cloud.common import Struct
from cloud.transport.server import TransportServerFactory

# run server
if __name__ == "__main__":
    # read the configuration
    f = open('config.yaml')
    configDict = yaml.load(f)
    f.close()
    config = Struct(configDict)
    
    # setup logging
    log.startLogging(sys.stdout)
    reactor.listenTCP(config.server.port, TransportServerFactory(config.commands, config.server.homedir))
    reactor.run()
