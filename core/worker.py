from twisted.internet import reactor
from twisted.internet import protocol

from multiprocessing import Queue

from cloud.core.common import *
from cloud.core.transport.worker import *
from cloud.core.transport.router import *

# Worker class
class Worker(object):
    # save the chunk
    def saveChunk(self, chunk):
        pass
    
    # process the chunk
    def cmap(self, chunkid):
        pass
    
    # downlink the chunk
    def downlink(self, chunkid):
        pass

# run the worker and twisted reactor
if __name__ == "__main__":
    fromRouterToWorker = Queue()
    fromWorkerToRouter = Queue()
    
    route_table = {}
    # start client and router
    reactor.connectTCP("localhost", 8000, TransportWorkerFactory(fromWorkerToRouter, fromRouterToWorker))
    reactor.listenTCP(8008, TransportRouterFactory(fromWorkerToRouter, fromRouterToWorker))
    print("Client and Router are up and running")
    reactor.run()
