import os
import math
import pickle
from uuid import uuid4
from PIL import Image

from twisted.python import log
from twisted.internet import task
from twisted.internet import reactor
from twisted.internet import protocol

from cloud.common import *

# split the remote sensing data into chunks
def splitImageIntoChunks(filename):
    metadata = []
    image = Image.open(filename)
    width = image.size[0]
    height = image.size[1]
    # create data subdirectory for this file
    directory = "/home/obulpathi/phd/cloud/data/master/" + filename.split(".")[0]
    os.mkdir(directory)
    count = 0 # chunk counter
    for y in range(0, int(math.ceil(float(height)/chunk_y))):
        for x in range(0, int(math.ceil(float(width)/chunk_x))):
            left = x * chunk_x
            top = y * chunk_y
            right = min((x+1) * chunk_x, width)
            bottom = min((y+1) * chunk_y, height)
            # box = (left, top, right, bottom)
            data = image.crop((left, top, right, bottom))
            chunkname = directory + "/" + str(count) + ".jpg"
            data.save(chunkname)
            size = os.stat(chunkname).st_size
            box = Box(left, top, right, bottom)
            chunk = Chunk(uuid4(), chunkname, size, box)
            metadata.append(chunk)
            count = count + 1
    return metadata

class TransportMasterProtocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory
        self.status = IDLE 
        
    # received data      
    def dataReceived(self, packetstring):
        packet = pickle.loads(packetstring)
        if packet.flags == REGISTER:
            self.registerWorker(packet)
        elif packet.flags == "STATE":
            self.gotState(packet)
        elif packet.flags == "GET_WORK":
            self.getWork(packet.source, packet.payload)
        elif packet.flags == GET_CHUNK:
            self.transmitChunk(packet.source)
        elif packet.flags == MISSION:
            self.gotMission(packet.payload)
        else:
            log.msg(packet)
            log.msg("Unknown stuff")
    
    # register worker
    def registerWorker(self, packet):
        log.msg("registered worker")
        self.factory.registrationCount = self.factory.registrationCount + 1
        packet = Packet(self.factory.address, self.factory.registrationCount, \
                        self.factory.address, self.factory.registrationCount, \
                        REGISTERED, self.factory.registrationCount, HEADERS_SIZE)
        packetstring = pickle.dumps(packet)
        self.transport.write(packetstring)
        self.status = REGISTERED
    
    # get mission
    def getMission(self):
        packet = Packet(self.factory.address, "Receiver", self.factory.address, "Server", \
                        GET_MISSION, None, HEADERS_SIZE)
        packetstring = pickle.dumps(packet)
        self.transport.write(packetstring)
    
    # got mission
    def gotMission(self, mission):
        self.factory.gotMission(mission)
        
    # get work to workers
    def getWork(self, worker, finishedWork = None):
        work = self.factory.getWork(worker, finishedWork)
        if not work:
            self.noWork(worker)
        else:
            self.sendWork(worker, work)
            
    # send no work message
    def noWork(self, destination):
        packet = Packet(self.factory.address, "Receiver", self.factory.address, destination, \
                        "NO_WORK", None, HEADERS_SIZE)
        packetstring = pickle.dumps(packet)
        self.transport.write(packetstring)

    # send work
    def sendWork(self, destination, work):
        packet = Packet(self.factory.address, "Receiver", self.factory.address, destination, \
                        "WORK", work, HEADERS_SIZE)
        packetstring = pickle.dumps(packet)
        self.transport.write(packetstring)
        
    # transmit chunk
    def transmitChunk(self, destination):
        log.msg("Master got request for chunk")
        image = open("chunk.jpg", "rb")
        data = image.read()
        chunk = Chunk("chunkid", "size", "box", data)
        packet = Packet(self.factory.address, "Receiver", self.factory.address, destination, \
                        CHUNK, chunk, HEADERS_SIZE)
        packetstring = pickle.dumps(packet)
        self.transport.write(packetstring)


# Master factory
class TransportMasterFactory(protocol.Factory):
    def __init__(self):
        self.status = "START"
        self.address = "Master"
        self.mission = None
        self.transports = []
        self.registrationCount = 0
        self.filepath = None
        try:
            os.mkdir("/home/obulpathi/phd/cloud/data/master")
        except OSError:
            pass
        task.deferLater(reactor, 1, self.getMission)
        
    def buildProtocol(self, addr):
        transport = TransportMasterProtocol(self)
        self.transports.append(transport)
        return transport
    
    def connected(self, transport):
        self.getMission()
        
    def getMission(self):
        for transport in self.transports:
            if transport.status == REGISTERED:
                transport.getMission()
                return                
        task.deferLater(reactor, 1, self.getMission)
    
    def gotMission(self, mission):
        if mission:
            self.execute(mission)
        else:
            task.deferLater(reactor, 1, self.getMission)

    def getWork(self, worker, oldWork = None):
        if oldWork:
            self.finishedWork(oldWork)
        if not self.mission:
            return None
        if self.mission.operation == SENSE:
            return None
        elif self.mission.operation == STORE:
            return self.getStoreWork(worker)
        elif self.mission.operation == PROCESS:
            return self.getProcessWork(worker)
        elif self.mission.operation == DOWNLINK:
            return self.getDownlinkWork(worker)
        else:
            log.msg("ERROR: Unknown mission: %s" % mission)
            return None
    
    def getStoreWork(self, worker):
        for chunk in self.chunks:
            if chunk.status == "UNASSIGNED":
                chunk.worker = worker
                chunk.status = "ASSIGNED"
                data = open(chunk.name).read()
                work = Work(chunk.uuid, "STORE", os.path.split(chunk.name)[1], data)
                log.msg(chunk)
                return work
        # no work: check if mission is complete
        if self.isMissionComplete():
            log.msg("Mission Accomplished")
            self.getMission()

    def finishedWork(self, work):
        for chunk in self.chunks:
            if chunk.uuid == work.uuid:
                log.msg(chunk.uuid)
                log.msg(work.uuid)
                chunk.status = "FINISHED" 
        
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
        log.msg(mission)
        source = open("data.jpg", "r")
        data = source.read()
        source.close() 
        sink = open(mission.filename, "w")
        sink.write(data)
        sink.close()
        self.mission = None
        # get next mission
        self.getMission()
    
    # store the given image on cdfs
    def store(self, mission):
        log.msg("Executing sensing mission: ")
        log.msg(mission)
        # split the image into chunks
        self.chunks = splitImageIntoChunks(mission.filename)
        # mission is ready to be executed
        self.mission = mission

    # process the given file and downlink
    def process(self, mission):
        log.msg(mission)
        log.msg("MapReduce mission")
        self.getMission()

    # downlink the given file
    def downlink(self, mission):
        log.msg(mission)
        log.msg("Torrent mission")
        self.getMission()

    # check if the current mission is complete
    def isMissionComplete(self):
        if self.mission.operation == SENSE:
            return self.isSenseMissionComplete()
        elif self.mission.operation == STORE:
            return self.isStoreMissionComplete()
        elif self.mission.operation == PROCESS:
            return self.isProcessMissionComplete()
        elif mission.operation == DOWNLINK:
            return self.isDownlinkMissionComplete()

    def isSenseMissionComplete(self):
        return False
        
    def isStoreMissionComplete(self):
        for chunk in self.chunks:
            if chunk.status != "FINISHED":
                return False
        return True
    
    def isProcessMissionComplete(self):
        return False
    
    def isDownlinkMissionComplete(self):
        return False
    
    def missionComplete(self):
        self.mission = None
        self.getMission()
