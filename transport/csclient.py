import math
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
        self.name = None
        self.mode = "LINE"
        self.line = None
        self.work = None
        self.fragments = None
        self.fragmentsLength = 0
        self.packetLength = 0
        self.waiter = WaitForData(self.factory.fromWorkerToCSClient, self.getData)
        self.waiter.start()
        self.mutex = Lock()
        self.setLineMode()

    def getData(self, data):       
        if self.mode == "LINE":
            # print(data)
            self.line = data
            fields = data.split(":")
            self.work = Work(fields[1], fields[2], fields[3], None)
            self.work.size = fields[4]
            self.work.fromstr(data)
            self.packetLength = int(self.work.size)
            self.fragments = None
            self.fragmentsLength = 0
            self.mode = "RAW"
        else:
            # buffer the the fragments
            if not self.fragments:
                self.fragments = data
                self.fragmentsLength = len(self.fragments)
            else:
                self.fragments = self.fragments + data
                self.fragmentsLength = self.fragmentsLength + len(data)
            # check if we received all the fragments
            if self.fragmentsLength == self.packetLength:
                self.mode = "LINE"
                self.sendChunk(self.line, self.fragments)

    def sendChunk(self, line, data):
        self.mutex.acquire()
        self.sendLine(line + LOREMIPSUM)
        self.setRawMode()
        length = len(data)
        for i in range(int(math.ceil(float(length)/MAX_PACKET_SIZE))):
            self.transport.write(data[i*MAX_PACKET_SIZE:(i+1)*MAX_PACKET_SIZE])
        self.setLineMode()
        self.mutex.release()
        log.msg("CS client: sent data to gsserver")
        
    def connectionMade(self):
        log.msg("Worker connection made")
        self.status = REGISTERED

    def lineReceived(self, line):
        log.msg("cs client received ack from gsserver")
        # self.factory.fromCSClientToWorker.put(line)
        
    def dataReceived(self, packetstring):
        self.factory.fromCSClientToWorker.put(packetstring)
        
    def register(self):
        packet = Packet("sender", "receiver", "worker", "Server", REGISTER, None, HEADERS_SIZE)
        data = pickle.dumps(packet)
        self.transport.write(data)
        
    def registered(self, packet):
        self.name = packet.payload
        self.status = REGISTERED
        
    def deregister(self):
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
