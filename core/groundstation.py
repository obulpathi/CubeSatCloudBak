from twisted.internet import reactor
from twisted.internet import protocol

from multiprocessing import Queue

from cloud.core.common import *
from cloud.core.transport.gsclient import *
from cloud.core.transport.gsserver import *

# run the worker and twisted reactor
if __name__ == "__main__":
    fromGSClientToGSServer = Queue()
    fromGSServerToGSClient = Queue()
    
    route_table = {}
    # start client and router
    reactor.connectTCP("localhost", 4000, TransportGSClientFactory(fromGSClientToGSServer, fromGSServerToGSClient))
    reactor.listenTCP(4004, TransportGSServerFactory(fromGSClientToGSServer, fromGSServerToGSClient))
    print("Client and Router are up and running")
    reactor.run()
