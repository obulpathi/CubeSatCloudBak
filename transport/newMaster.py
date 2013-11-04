import os
import math
import time
import pickle
from time import sleep
from threading import Lock

from twisted.python import log
from twisted.internet import task
from twisted.internet import reactor
from twisted.internet import protocol
from twisted.protocols.basic import LineReceiver

from cloud import utils
from cloud.common import *
from cloud.transport.transport import MyTransport

class TransportMasterProtocol(LineReceiver):
    def __init__(self, factory):
        self.factory = factory
        self.status = IDLE
        self.mode = "LINE"
        #self.MAX_LENGTH = 64000
        self.mutexpr = Lock()
        self.mutexsp = Lock()
        self.setLineMode()
        # self.mytransport = MyTransport(self, "Master")
    
    # line received
    def lineReceived(self, line):
        log.msg("line received")
        fields = line.split(":")
        command = fields[0]
        if command == "REGISTER":
            self.registerWorker(fields[1])
        elif command == "WORK":
            if fields[2]:
                work = Work(fields[2], fields[3], fields[4], None)
                self.getWork(fields[1], work)            
            else:
                self.getWork(fields[1], None)
        else:
            print "Garbage: ", line
            
    def lineLengthExceeded(self, line):
        log.msg("################################################")
                                       
    # received a packet
    def packetReceived(self, packet):
        self.mutexpr.acquire()
        log.msg(packet)
        if packet.flags == REGISTER:
            self.registerWorker(packet)
        elif packet.flags == "STATE":
            self.gotState(packet)
        elif packet.flags == "GET_WORK":
            self.getWork(packet.source, packet.payload)
        elif packet.flags == GET_CHUNK:
            self.transmitChunk(packet.source)
        else:
            log.msg(packet)
            log.msg("Unknown stuff")
        self.mutexpr.release()

    # send a packet, if needed using multiple fragments
    def sendPacket(self, packetstring):
        self.mutexsp.acquire()
        length = len(packetstring)
        packetstring = str(length).zfill(LHSIZE) + packetstring
        for i in range(int(math.ceil(float(length)/MAX_PACKET_SIZE))):
            self.transport.write(packetstring[i*MAX_PACKET_SIZE:(i+1)*MAX_PACKET_SIZE])
        self.mutexsp.release()
                
    # register worker
    def registerWorker(self, worker):
        self.factory.registerWorker(worker, self)
        self.status = REGISTERED
        
    # get work to workers
    def getWork(self, worker, finishedWork = None):
        work, data = self.factory.getWork(worker, finishedWork)
        if not work:
            self.noWork(worker)
        else:
            self.sendWork(work, data)
            
    # send no work message
    def noWork(self, destination):
        self.sendLine("NO_WORK")
    
    def sendWork(self, chunks, data):
        print chunks
        print "###############################"
        metadata = ""
        print len(chunks)
        print chunks
        for chunk in chunks:
            print chunk
            # metadata = metadata + "!"
            metadata = metadata + ":" + chunk.name + ":" + chunk.size
        print "stiched metadata"
        data = None
        for chunk in chunks:
            print "chunk"
            fragment = open("~/cloud/data/master/" + chunk.name).read()
            if not data:
                data = fragment
            else:
                data = data + fragment
        print "stiched data"
        metadata = str(len(data)) + ":"
        print "sending line"
        self.sendLine(metadata)
        print "sending data"
        self.sendData(data)
        print "sent data"
        
    def sendData(self, data):
        self.setRawMode()
        length = len(data)
        for i in range(int(math.ceil(float(length)/MAX_PACKET_SIZE))):
            self.transport.write(data[i*MAX_PACKET_SIZE:(i+1)*MAX_PACKET_SIZE])
                 
    # send work
    def sendWorkOld(self, work, data):
        log.msg("Sending work to worker")
        metadata = work.tostr()
        # + LOREMIPSUM
        log.msg("finished serilization")
        log.msg(metadata)
        log.msg("sending line")
        self.sendLine("WORK:" + metadata + LOREMIPSUM)
        log.msg("sending data")
        if work.job == "STORE":
            self.sendData(data)
        log.msg("Sent work to worker")
        # self.sendLine("DYMMY")
    
    def sendDataOld(self, data):
        self.setRawMode()
        length = len(data)
        for i in range(int(math.ceil(float(length)/MAX_PACKET_SIZE))):
            self.transport.write(data[i*MAX_PACKET_SIZE:(i+1)*MAX_PACKET_SIZE])
        self.setLineMode()

# Master factory
class TransportMasterFactory(protocol.Factory):
    def __init__(self):
        self.state = "START"
        self.name = "Master"
        self.mission = None
        self.workers = {}
        self.transports = []
        self.registrationCount = 0
        self.homedir = os.path.expanduser(homedir)
        self.metadir = self.homedir + "metadata/"
        self.mutex = Lock()
        self.fileMap = {}
        self.metadata = {}
        self.missions = ["SENSE:image.jpg:1:latitude:longitude", "STORE:image.jpg:2:", "DOWNLINK:image.jpg:3:"]
    
        try:
            os.mkdir(self.homedir)
            os.mkdir(self.metadir)
        except OSError:
            pass
        self.fromMasterToMasterClient = fromMasterToMasterClient
        self.fromMasterClientToMaster = fromMasterClientToMaster
        self.waiter = WaitForData(self.fromMasterClientToMaster, self.getData)
        self.waiter.start()
        self.startTime = time.time()

    def buildProtocol(self, addr):
        return TransportMasterProtocol(self)
