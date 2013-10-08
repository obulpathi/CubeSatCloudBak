import pickle
from threading import Lock

from twisted.python import log
from twisted.internet import task
from twisted.internet import reactor
from twisted.internet import protocol
from twisted.protocols.basic import LineReceiver

from cloud import utils
from cloud.common import *

class TransportCSClientProtocol(LineReceiver):
    def __init__(self, factory):
        self.factory = factory
        self.id = None
        self.mode = "LINE"
        self.waiter = WaitForData(self.factory.fromWorkerToCSClient, self.getData)
        self.waiter.start()
        self.mutexsp = Lock()

    def getData(self, data):
        if self.mode == "LINE":
            self.sendLine(data)
            self.mode = "RAW"
            self.setRawMode()
        else:
            self.transport.write(data)
            self.mode = "LINE"
            self.setLineMode()

    def connectionMade(self):
        log.msg("Worker connection made")
        self.status = REGISTERED
    
    def dataReceived(self, packetstring):
        self.factory.fromCSClientToWorker.put(packetstring)
    
    # send a packet, if needed using multiple fragments
    def sendPacket(self, packetstring):
        self.mutexsp.acquire()
        length = len(packetstring)
        packetstring = str(length).zfill(LHSIZE) + packetstring
        for i in range(int(math.ceil(float(length)/MAX_PACKET_SIZE))):
            self.transport.write(packetstring[i*MAX_PACKET_SIZE:(i+1)*MAX_PACKET_SIZE])
        self.mutexsp.release()
        
    def register1(self):
        packet = Packet("sender", "receiver", "worker", "Server", REGISTER, None, HEADERS_SIZE)
        data = pickle.dumps(packet)
        self.transport.write(data)
        
    def registered1(self, packet):
        log.msg("Whoa!!!!!")
        self.id = packet.payload
        self.status = REGISTERED
        
    def deregister1(self):
        self.transport.loseConnection()
        
            
class TransportCSClientFactory(protocol.ClientFactory):
    def __init__(self, fromWorkerToCSClient, fromCSClientToWorker):
        self.fromWorkerToCSClient = fromWorkerToCSClient
        self.fromCSClientToWorker = fromCSClientToWorker
        
    def buildProtocol(self, addr):
        return TransportCSClientProtocol(self)
        
    def clientConnectionFailed(self, connector, reason):
        log.msg("Connection failed.")
        reactor.stop()
        
    def clientConnectionLost(self, connector, reason):
        log.msg("Connection lost.")
        reactor.stop()
