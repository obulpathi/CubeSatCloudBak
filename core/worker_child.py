import threading
from threading import Thread
from twisted.internet import reactor

from cloud.core.transport_client import *
from cloud.core.transport_router import *

class Worker(object):
    pass
    
class TransportClient(threading.Thread):
    def __init__(self, host, port):
        reactor.connectTCP(host, port, TransportClientFactory())
        threading.Thread.__init__(self)
    def run(self):
        pass

class TransportRouter(threading.Thread):
    def __init__(self, port):
        reactor.listenTCP(port, TransportRouterFactory())
        threading.Thread.__init__(self)
    def run(self):
        pass
        
if __name__ == "__main__":
    worker = Worker()
    client = TransportClient("localhost", 8008)
    router = TransportRouter(8016)
    twistedThread = Thread(target=reactor.run, args = (False,));
    twistedThread.start()
    print("Client and Router are up and running")
