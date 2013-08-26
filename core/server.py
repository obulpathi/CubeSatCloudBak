from twisted.internet import reactor
from twisted.internet import protocol

from cloud.core.common import *
from cloud.core.transport.server import *
from cloud.core.transport.csclient import *

# run server
if __name__ == "__main__":
    reactor.listenTCP(4000, TransportServerFactory())
    print("Server is up and running")
    reactor.run()
