import sys
import yaml

from twisted.python import log
from twisted.internet import reactor
from twisted.internet import protocol

from cloud.common import *
from cloud.transport.server import *

# run server
if __name__ == "__main__":
    # read configuration
    f = open('config.yaml')
    configDict = yaml.load(f)
    f.close()
    config = Struct(configDict)
    # setup logging
    # log.startLogging(open('/var/log/server.log', 'w'))
    log.startLogging(sys.stdout)
    reactor.listenTCP(config.server.port, TransportServerFactory(config.missions))
    log.msg(config.missions)
    reactor.run()
