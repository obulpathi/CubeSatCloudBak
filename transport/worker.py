import os
import pickle

from twisted.python import log
from twisted.internet import task
from twisted.internet import reactor
from twisted.internet import protocol

from cloud.common import *

class TransportWorkerProtocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory
        self.address = "Worker"
        self.cswaiter = WaitForData(self.factory.fromCSServerToWorker, self.getData)
        self.ccwaiter = WaitForData(self.factory.fromCSClientToWorker, self.getData)
        self.cswaiter.start()
        self.ccwaiter.start()
        self.filepath = "/home/obulpathi/phd/cloud/data/"

    def getData(self, data):
        self.transport.write(data)

    def connectionMade(self):
        log.msg("Worker connection made")
        self.register()
    
    def dataReceived(self, packetstring):
        packet = pickle.loads(packetstring)
        if self.address == "Worker" and packet.flags & REGISTERED:
            self.registered(packet)
        elif packet.destination == "Server":
            self.forwardToServer(packetstring)
        elif packet.destination != self.address:
            self.forwardToChild(packet)
        elif packet.flags == "NO_WORK":
            self.noWork()
        elif packet.flags == "WORK":
            self.gotWork(packet.payload)
        elif packet.flags & CHUNK:
            self.receivedChunk(packet)
        else:
            log.msg("Server said: %s" % packetstring)
    
    def register(self):
        packet = Packet("Worker", "Server", "Worker", "Server", REGISTER, None, HEADERS_SIZE)
        data = pickle.dumps(packet)
        self.transport.write(data)
        
    def registered(self, packet):
        self.address = packet.payload
        self.filepath = self.filepath + str(self.address) + "/"
        try:
            os.mkdir(self.filepath)
        except OSError:
            pass
        self.status = IDLE
        self.getWork()
        
    def deregister(self):
        self.transport.loseConnection()

    def getWork(self):
        packet = Packet(self.address, "Receiver", self.address, "Server", "GET_WORK", None, HEADERS_SIZE)
        data = pickle.dumps(packet)
        self.transport.write(data)
    
    def noWork(self):
        log.msg("No work")
        task.deferLater(reactor, 1, self.getWork)
    
    def gotWork(self, work):
        if work.job == "STORE":
            self.store(work.filename, work.payload)
        elif work.jpb == "PROCESS":
            log.msg("TODO: >>>>>>>>>>>>>>>>>>>>>>>>>>>")
        elif work.job == "DOWNLINK":
            log.msg("TODO: >>>>>>>>>>>>>>>>>>>>>>>>>>")
        else:
            log.msg("Unkown work")
            log.msg(work)

    def store(self, filename, data):
        # modify the filename here
        log.msg(self.filepath)
        log.msg(filename)
        chunk = open(self.filepath + filename, "w")
        chunk.write(data)
        chunk.close()
        self.getWork()
        
    def forwardToServer(self, packetstring):
        self.factory.fromWorkerToCSClient.put(packetstring)
            
    def forwardToChild(self, packet):
        self.factory.fromWorkerToCSServer.put(packet)
        
    def requestChunk(self):
        log.msg("requesting chunk")
        packet = Packet(self.id, "receiver", self.id, "Server", GET_CHUNK, None, HEADERS_SIZE)
        data = pickle.dumps(packet)
        self.transport.write(data)
    
    def receivedChunk(self, packet):
        log.msg("Chunk received")
        chunk = open("chunk1.jpg", "wb")
        chunk.write(packet.payload.data)
        chunk.close()

            
class TransportWorkerFactory(protocol.ClientFactory):
    def __init__(self, fromWorkerToCSClient, fromCSClientToWorker, fromWorkerToCSServer, fromCSServerToWorker):
        self.fromWorkerToCSClient = fromWorkerToCSClient
        self.fromCSClientToWorker = fromCSClientToWorker
        self.fromWorkerToCSServer = fromWorkerToCSServer
        self.fromCSServerToWorker = fromCSServerToWorker
        
    def buildProtocol(self, addr):
        return TransportWorkerProtocol(self)
        
    def clientConnectionFailed(self, connector, reason):
        log.msg("Connection failed.")
        reactor.stop()
        
    def clientConnectionLost(self, connector, reason):
        log.msg("Connection lost.")
        reactor.stop()
