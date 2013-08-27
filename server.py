import sys

from twisted.python import log
from twisted.internet import reactor
from twisted.internet import protocol

from cloud.common import *
from cloud.transport.server import *

# run server
if __name__ == "__main__":
    # log.startLogging(open('/var/log/server.log', 'w'))
    log.startLogging(sys.stdout)
    reactor.listenTCP(4000, TransportServerFactory())
    log.msg("Server is up and running")
    reactor.run()
