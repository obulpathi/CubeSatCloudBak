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
    def __init__(self, homedir, fromMasterToMasterClient, fromMasterClientToMaster):
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

    def getData(self, packet):
        log.msg("Master got line: %s" % packet)
        fields = packet.split(":")
        command = fields[0]
        if command == "REGISTER":
            self.registerMasterClient()
        elif command == "MISSION":
            mission = Mission()
            mission.operation = fields[1]
            mission.filename = fields[2]
            mission.uuid = fields[3]
            if mission.operation == "PROCESS":
                mission.output = fields[4]
            self.gotMission(mission)
        else:
            log.msg("Received unknown packet from Master Client")
            log.msg(packet)

    def sendData(self, data):
        log.msg("Master sending line to MasterClient: %s" % data)
        self.fromMasterToMasterClient.put(data)
    
    def sendMetadata(self, metadata):
        data = "METADATA:" + metadata.tostr()
        self.sendData(data)
        # log.msg("Sent metadata")

    def buildProtocol(self, addr):
        transport = TransportMasterProtocol(self)
        self.transports.append(transport)
        return transport
    
    def registerMasterClient(self):
        log.msg("Registered Master Client")
        self.getMission()

    def registerWorker(self, worker, transport):
        self.workers[worker] = WorkerState(worker, transport)
        log.msg("Registered worker: " + worker)
        task.deferLater(reactor, 1, self.getMission)
                
    def getMission(self):
        mission = None
        if self.missions:
            log.msg("Operation time: %s" % str(time.time() - self.startTime))
            mission = Mission()
            mission.fromstr(self.missions.pop(0))
        task.deferLater(reactor, 1, self.gotMission, mission)
        """
        data = "GET_MISSION:NONE" + LOREMIPSUM
        self.fromMasterToMasterClient.put(data)
        """

    def gotMission(self, mission):
        if mission:
            log.msg("Got mission")
            log.msg(mission)
            self.execute(mission)
        else:
            log.msg("No mission")
            task.deferLater(reactor, 5, self.getMission)
    
    def execute(self, mission):
        log.msg("Received mission: %s" % mission)
        if mission.operation == SENSE:
            self.sense(mission)
        elif mission.operation == STORE:
            self.store(mission)
        elif mission.operation == PROCESS:
            self.process(mission)
        elif mission.operation == DOWNLINK:
            self.downlink(mission)
        else:
            log.msg("ERROR: Unknown mission: %s" % mission)

    # simulate sensing
    def sense(self, mission):
        log.msg("Executing sensing mission: ")
        source = open("data.jpg", "r")
        data = source.read()
        source.close()
        log.msg("Read from source")
        sink = open(mission.filename, "w")
        sink.write(data)
        sink.close()
        log.msg("Wrote to sink")
        self.senseMissionComplete(mission)
    
    # store the given image on cdfs
    def store(self, mission):
        log.msg("Executing storing mission")
        # split the image into chunks
        self.chunks, self.metadata = utils.splitImageAndCode(mission.filename, self.homedir)
        log.msg("Created chunks")
        # self.chunks, self.metadata = utils.splitImageIntoChunks(mission.filename, self.homedir)
        # assign work to workers, using Uniform Load balancer
        utils.uniformLoadBalancer(self.workers, self.chunks, self.metadata)
        log.msg("performed load balancing")
        # mission is ready to be executed
        self.mission = mission
        log.msg("starting storing operation")
        self.startStoreOperation()

    # process the given file and downlink
    def process(self, mission):
        self.mission = mission
        self.loadMetadata(mission.filename)
        log.msg("MapReduce mission")

    # downlink the given file
    def downlink(self, mission):
        log.msg(mission)
        self.loadMetadata(mission.filename)
        self.mission = mission

    # load the metadata for the file
    def loadMetadata(self, filename):
        self.metadata = self.fileMap[filename]
        chunkMap = self.metadata.chunkMap
        for chunks in chunkMap.itervalues():
            for chunk in chunks:
                chunk.status = "UNASSIGNED"
    
    # start store operation
    def startStoreOperation(self):
        for worker in self.workers:
            work, data = self.getWork(worker)
            self.workers[worker].transport.sendWork(work, data)
        
    def getWork(self, worker, oldWork = None):
        self.mutex.acquire()
        work = None
        data = None
        # log.msg("Work requested by worker")
        if oldWork:
            self.finishedWork(oldWork, worker)
        if not self.mission:
            pass
        elif self.mission.operation == SENSE:
            pass
        elif self.mission.operation == STORE:
            work, data = self.getStoreWork(worker)
        elif self.mission.operation == PROCESS:
            work, data = self.getProcessWork(worker)
        elif self.mission.operation == DOWNLINK:
            work, data = self.getDownlinkWork(worker)
        else:
            log.msg("ERROR: Unknown mission: %s" % mission)
        self.mutex.release()
        return work, data
    
    def getStoreWork(self, worker):
        log.msg("Store work requested by worker")
        directory = self.metadata.directory
        chunkMap = self.metadata.chunkMap
        chunks = chunkMap.get(worker, [])
        metadata = "tmp"
        for chink in chunks:
            print chick
            metadata = metadata + ":" + chink.name + ":" + chick.size
            print "yey"
        log.msg("returning the chunks")
        return metadata, None
        """
        # print len(chunks)
        for chunk in chunks:
            if chunk.status == "UNASSIGNED":
                chunk.status = "ASSIGNED"
                chunk.worker = worker
                data = open(directory + chunk.name).read()
                work = Work(chunk.uuid, "STORE", chunk.name, None)
                work.size = chunk.size
                log.msg(work)
                print "returning work to worker"
                return work, data
        # no work: set a callback to check if mission is complete and return
        task.deferLater(reactor, 0.15, self.isMissionComplete)
        return None, None
        """

    def getProcessWork(self, worker):
        # log.msg("Process work requested by worker")
        chunkMap = self.metadata.chunkMap
        chunks = chunkMap.get(worker, [])
        for chunk in chunks:
            if chunk.status == "UNASSIGNED":
                chunk.status = "ASSIGNED"
                work = Work(chunk.uuid, "PROCESS", chunk.name, self.mission.output.split(".")[0])
                log.msg(work)
                return work, None
        # no work: check if mission is complete
        if self.isProcessMissionComplete():
            self.processMissionComplete(self.mission)
        return None, None
        
    def getDownlinkWork(self, worker):
        # log.msg("Downlink work requested by worker")
        chunkMap = self.metadata.chunkMap
        chunks = chunkMap.get(worker, [])
        for chunk in chunks:
            if chunk.status == "UNASSIGNED":
                chunk.status = "ASSIGNED"
                work = Work(chunk.uuid, "DOWNLINK", chunk.name, None)
                log.msg(work)
                return work, None
        # no work: check if mission is complete
        task.deferLater(reactor, 0.15, self.isDownlinkMissionComplete)
        return  None, None
        
    def finishedWork(self, work, worker):
        if self.mission.operation == STORE:
            self.finishedStoreWork(work)
        elif self.mission.operation == PROCESS:
            self.finishedProcessWork(work, worker)
        elif self.mission.operation == DOWNLINK:
            self.finishedDownlinkWork(work, worker)
        else:
            log.msg("ERROR: Unknown mission")
            log.msg(work)

    def finishedStoreWork(self, work):
        chunk = self.chunks[work.uuid]
        chunkMap = self.metadata.chunkMap
        if chunkMap.get(chunk.worker):
            chunkMap[chunk.worker].append(chunk)
        else:
            chunkMap[chunk.worker] = [chunk]
        del self.chunks[work.uuid]
    
    def finishedProcessWork(self, work, worker):
        chunkMap = self.metadata.chunkMap
        chunks = chunkMap[worker]
        for chunk in chunks:
            if chunk.uuid == work.uuid:
                chunk.status = "FINISHED"
                return
        log.msg("ERROR: Got unknown work item")
            
    def finishedDownlinkWork(self, work, worker):
        chunkMap = self.metadata.chunkMap
        chunks = chunkMap[worker]
        for chunk in chunks:
            if chunk.uuid == work.uuid:
                chunk.status = "FINISHED"
                return
        log.msg("ERROR: Got unknown work item")
        
    # check if the current mission is complete
    # and if it is, get a new misison
    def isMissionComplete(self):
        if not self.mission:
            return True
        elif self.mission.operation == SENSE:
            return self.isSenseMissionComplete()
        elif self.mission.operation == STORE:
            if self.isStoreMissionComplete():
                self.mission = None
                self.storeMissionComplete()
                return True
        elif self.mission.operation == PROCESS:
            return self.isProcessMissionComplete()
        elif self.mission.operation == DOWNLINK:
            return self.isDownlinkMissionComplete()
            self.mission = None
            self.downlinkMissionComplete()

    def isSenseMissionComplete(self):
        return False
        
    def isStoreMissionComplete(self):
        if self.chunks:
            return False
        return True
    
    def isProcessMissionComplete(self):
        chunkMap = self.metadata.chunkMap
        for chunks in chunkMap.itervalues():
            for chunk in chunks:
                if chunk.status != "FINISHED":
                    return False
        return True
    
    def isDownlinkMissionComplete(self):
        chunkMap = self.metadata.chunkMap
        for chunks in chunkMap.itervalues():
            for chunk in chunks:
                if chunk.status != "FINISHED":
                    return False
        self.downlinkMissionComplete(self.mission)
        return True

    def senseMissionComplete(self, mission):
        log.msg("Sense Mission Accomplished")
        self.missionComplete(mission)
            
    def storeMissionComplete(self):
        log.msg("Store Mission Accomplished")
        # send the metadata
        self.fileMap[self.metadata.filename] = self.metadata
        # self.sendMetadata(self.metadata)
        # self.metadata.save(self.metadir)
        task.deferLater(reactor, 1, self.missionComplete, self.mission)
        #self.missionComplete(self.mission)

    def processMissionComplete(self, mission):
        log.msg("Process Mission Accomplished")
        log.msg(mission)
        subdirname = mission.output.split(".")[0] + "/"
        # making changes to metadata
        chunkMap = self.metadata.chunkMap
        for chunks in chunkMap.itervalues():
            for chunk in chunks:
                chunk.name = subdirname + os.path.split(chunk.name)[1]
        self.metadata.directory = os.path.split(self.metadata.directory)[0] + "/" + subdirname
        self.metadata.filename = mission.output
        # send the metadata
        # log.msg("sending metadata")
        self.fileMap[self.metadata.filename] = self.metadata
        #self.sendMetadata(self.metadata)
        self.metadata.save(self.metadir)
        task.deferLater(reactor, 1, self.getMission)
        
    def downlinkMissionComplete(self, mission):
        log.msg("Downlink Mission Accomplished")
        self.fileMap[self.metadata.filename] = self.metadata
        self.sendMetadata(self.metadata)
        self.metadata.save(self.metadir)
        task.deferLater(reactor, 1, self.missionComplete, mission)

    # send a notification that current mission is complete and fetch next    
    def missionComplete(self, mission):
        print("MISSION COMPLETE")
        self.getMission()
        #self.sendData("GET_MISSION:")
        #self.sendData("GET_MISSION:" + mission.tostr())
        self.mission = None
