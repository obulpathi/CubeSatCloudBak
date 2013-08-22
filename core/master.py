import threading
from threading import Thread
from twisted.internet import reactor

from cloud.core.transport_server import *

class Master(object):
    pass
    
class TransportServer(threading.Thread):
    def __init__(self, port):
        reactor.listenTCP(port, TransportServerFactory())
        threading.Thread.__init__(self)
        
    def run(self):
        pass

    def transmit(self, data):
        pass

if __name__ == "__main__":
    master = Master()
    server = TransportServer(8000)
    twistedThread = Thread(target=reactor.run, args = (False,));
    twistedThread.start()
    print("Master is up and running")
