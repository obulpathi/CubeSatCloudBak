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
        self.getWork(None)
        
    def deregister(self):
        self.transport.loseConnection()

    def getWork(self, work):
        packet = Packet(self.address, "Receiver", self.address, "Server", "GET_WORK", work, HEADERS_SIZE)
        data = pickle.dumps(packet)
        self.transport.write(data)
    
    def noWork(self):
        log.msg("No work")
        task.deferLater(reactor, 1, self.getWork, None)
    
    def gotWork(self, work):
        if work.job == "STORE":
            self.store(work)
        elif work.job == "PROCESS":
            log.msg("PROCESS TODO: >>>>>>>>>>>>>>>>>>>>>>>>>>>")
        elif work.job == "DOWNLINK":
            self.downlink(work)
        else:
            log.msg("Unkown work")
            log.msg(work)

    def store(self, work):
        # modify the filename here
        chunk = open(self.filepath + work.filename, "w")
        chunk.write(work.payload)
        chunk.close()
        self.getWork(Work(work.uuid, work.job, work.filename, None))
    
    def downlink(self, work):
        log.msg(work.filename)
        chunk = open(self.filepath + work.filename, "r")
        data = chunk.read()
        chunk.close()
        new_work = Work(work.uuid, work.job, work.filename, data)
        packet = Packet(self.address, "Receiver", self.address, "Server", CHUNK, new_work, HEADERS_SIZE)
        self.forwardToServer(pickle.dumps(packet))
        self.getWork(Work(work.uuid, work.job, work.filename, None))
                   
    def forwardToServer(self, packetstring):
        self.factory.fromWorkerToCSClient.put(packetstring)
            
    def forwardToChild(self, packet):
        self.factory.fromWorkerToCSServer.put(packet)

            
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
