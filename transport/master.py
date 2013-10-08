import os
import math
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
        self.mutexpr = Lock()
        self.mutexsp = Lock()
        self.mytransport = MyTransport(self, "Master")
        
    # received data
    """
    def dataReceived(self, fragment):
        self.mytransport.dataReceived(fragment)
    """
    
    # line received
    def lineReceived(self, line):
        fields = line.split(":")
        command = fields[0]
        if command == "REGISTER":
            self.registerWorker()
        elif command == "WORK":
            if fields[2]:
                work = Work(fields[2], fields[3], fields[4], None)
                self.getWork(fields[1], work)            
            else:
                self.getWork(fields[1], None)
        else:
            print(line)
                                    
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
            utils.banner("Unknown stuff")
        self.mutexpr.release()

    # send a packet, if needed using multiple fragments
    def sendPacket(self, packetstring):
        self.mutexsp.acquire()
        length = len(packetstring)
        packetstring = str(length).zfill(LHSIZE) + packetstring
        for i in range(int(math.ceil(float(length)/MAX_PACKET_SIZE))):
            log.msg("Sending a fragment")
            self.transport.write(packetstring[i*MAX_PACKET_SIZE:(i+1)*MAX_PACKET_SIZE])
        self.mutexsp.release()
                
    # register worker
    # def registerWorker(self, packet):
    def registerWorker(self):        
        log.msg("registered worker")
        self.factory.registrationCount = self.factory.registrationCount + 1
        """
        packet = Packet(self.factory.address, self.factory.registrationCount, 
                        self.factory.address, self.factory.registrationCount, 
                        REGISTERED, self.factory.registrationCount, HEADERS_SIZE)
        packetstring = pickle.dumps(packet)
        self.sendPacket(packetstring)
        """
        self.sendLine("REGISTERED:" + str(self.factory.registrationCount))
        utils.banner("REGISTER")
        self.status = REGISTERED
        
    # get work to workers
    def getWork(self, worker, finishedWork = None):
        utils.banner("GET WORK")
        work, data = self.factory.getWork(worker, finishedWork)
        if not work:
            self.noWork(worker)
        else:
            self.sendWork(work, data)
            
    # send no work message
    def noWork(self, destination):
        self.sendLine("NO_WORK")
        utils.banner("NO_WORK")
        
        """
        packet = Packet(self.factory.address, "Receiver",
                        self.factory.address, destination,
                        "NO_WORK", None, HEADERS_SIZE)
        packetstring = pickle.dumps(packet)
        self.sendPacket(packetstring)
        """
        
    # send work
    def sendWork(self, work, data):
        utils.banner("WORK")
        metadata = work.tostr()
        self.sendLine("WORK:" + metadata)
        if work.job == "STORE":
            self.sendData(data)
    
    def sendData(self, data):
        self.setRawMode()
        self.transport.write(data)
        self.setLineMode()
        
        """
        packet = Packet(self.factory.address, "Receiver",
                        self.factory.address, destination,
                        "WORK", work, HEADERS_SIZE)
        packetstring = pickle.dumps(packet)
        self.sendPacket(packetstring)
        """

# Master factory
class TransportMasterFactory(protocol.Factory):
    def __init__(self, homedir, fromMasterToMasterClient, fromMasterClientToMaster):
        self.status = "START"
        self.address = "Master"
        self.mission = None
        self.transports = []
        self.registrationCount = 0
        self.homedir = os.path.expanduser(homedir)
        self.metadir = self.homedir + "metadata/"
        self.fileMap = {}
        self.metadata = {}
        try:
            os.mkdir(self.homedir)
            os.mkdir(self.metadir)
        except OSError:
            pass
        self.fromMasterToMasterClient = fromMasterToMasterClient
        self.fromMasterClientToMaster = fromMasterClientToMaster
        self.waiter = WaitForData(self.fromMasterClientToMaster, self.getData)
        self.waiter.start()

    def getData(self, packet):
        log.msg(packet)
        fields = packet.split(":")
        command = fields[0]
        if command == "REGISTER":
            self.registerMasterClient()
        elif command == "MISSION":
            mission = Mission()
            mission.operation = fields[1]
            mission.filename = fields[2]
            mission.uuid = fields[3]
            self.gotMission(mission)
        else:
            log.msg("Received unknown packet from Master Client: >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            log.msg(packet)

    def sendData(self, data):
        utils.banner("MASTER TO MASTER CLIENT ################################")
        self.fromMasterToMasterClient.put(data)
    
    def sendMetadata(self, metadata):
        print(metadata)
        utils.banner("METADATA")
        self.sendData("METADATA")
        log.msg("Sent metadata")
                            
    def buildProtocol(self, addr):
        transport = TransportMasterProtocol(self)
        self.transports.append(transport)
        return transport
    
    def registerMasterClient(self):
        log.msg("Do registritation stuff here")
        self.getMission()
            
    def getMission(self):
        utils.banner("Requesting for NEW_MISSION")
        log.msg("Requesting for new mission")
        data = "GET_MISSION"
        self.fromMasterToMasterClient.put(data)
        """
        packet = Packet("Master", "Receiver",
                        "Master", "Server", 
                        GET_MISSION, None, HEADERS_SIZE)
        self.fromMasterToMasterClient.put(packet)
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
        log.msg("Executing storing mission: ")
        # split the image into chunks
        self.chunks, self.metadata = utils.splitImageIntoChunks(mission.filename, self.homedir)
        # mission is ready to be executed
        self.mission = mission

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
        chunkMap = self.metadata["chunkMap"]
        for chunks in chunkMap.itervalues():
            for chunk in chunks:
                chunk.status = "UNASSIGNED"

    def getWork(self, worker, oldWork = None):
        log.msg("Work requested by worker")
        if oldWork:
            self.finishedWork(oldWork, worker)
        if not self.mission:
            return None, None
        if self.mission.operation == SENSE:
            return None, None
        elif self.mission.operation == STORE:
            return self.getStoreWork(worker)
        elif self.mission.operation == PROCESS:
            return self.getProcessWork(worker)
        elif self.mission.operation == DOWNLINK:
            return self.getDownlinkWork(worker)
        else:
            log.msg("ERROR: Unknown mission: %s" % mission)
            return None, None
    
    def getStoreWork(self, worker):
        log.msg("Store work requested by worker")
        directory = self.metadata["directory"]
        for chunk in self.chunks.itervalues():
            if chunk.status == "UNASSIGNED":
                chunk.worker = worker
                chunk.status = "ASSIGNED"
                data = open(directory + chunk.name).read()
                work = Work(chunk.uuid, "STORE", chunk.name, None)
                log.msg(chunk)
                return work, data
        # no work: set a callback to check if mission is complete and return
        task.deferLater(reactor, 0.15, self.isMissionComplete)
        return None, None

    def getProcessWork(self, worker):
        log.msg("Process work requested by worker")
        chunkMap = self.metadata["chunkMap"]
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
        log.msg("Downlink work requested by worker")
        chunkMap = self.metadata["chunkMap"]
        chunks = chunkMap.get(worker, [])
        for chunk in chunks:
            if chunk.status == "UNASSIGNED":
                chunk.status = "ASSIGNED"
                work = Work(chunk.uuid, "DOWNLINK", chunk.name, None)
                log.msg(work)
                return work, None
        # no work: check if mission is complete
        if self.isDownlinkMissionComplete():
            self.downlinkMissionComplete(self.mission)
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
        chunkMap = self.metadata["chunkMap"]
        if chunkMap.get(chunk.worker):
            chunkMap[chunk.worker].append(chunk)
        else:
            chunkMap[chunk.worker] = [chunk]
        del self.chunks[work.uuid]
    
    def finishedProcessWork(self, work, worker):
        chunkMap = self.metadata["chunkMap"]
        chunks = chunkMap[worker]
        for chunk in chunks:
            if chunk.uuid == work.uuid:
                chunk.status = "FINISHED"
                return
        log.msg("ERROR: Got unknown work item")
            
    def finishedDownlinkWork(self, work, worker):
        chunkMap = self.metadata["chunkMap"]
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
        chunkMap = self.metadata["chunkMap"]
        for chunks in chunkMap.itervalues():
            for chunk in chunks:
                if chunk.status != "FINISHED":
                    return False
        return True
    
    def isDownlinkMissionComplete(self):
        chunkMap = self.metadata["chunkMap"]
        for chunks in chunkMap.itervalues():
            for chunk in chunks:
                if chunk.status != "FINISHED":
                    return False
        return True

    def senseMissionComplete(self, mission):
        log.msg("Sense Mission Accomplished")
        self.missionComplete(mission)
            
    def storeMissionComplete(self):
        log.msg("Store Mission Accomplished")
        # send the metadata
        self.fileMap[self.metadata["filename"]] = self.metadata
        # FIX THIS >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>..
        # self.sendMetadata(self.metadata)
        utils.saveMetadata(self.metadata, self.metadir)
        #task.deferLater(reactor, 0.1, self.missionComplete, self.mission)
        self.missionComplete(self.mission)

    def processMissionComplete(self, mission):
        log.msg("Process Mission Accomplished")
        log.msg(self.metadata)
        log.msg(mission)
        subdirname = mission.output.split(".")[0] + "/"
        # making changes to metadata
        chunkMap = self.metadata["chunkMap"]
        for chunks in chunkMap.itervalues():
            for chunk in chunks:
                chunk.name = subdirname + os.path.split(chunk.name)[1]
        self.metadata["directory"] = os.path.split(self.metadata["directory"])[0] + "/" + subdirname
        self.metadata["filename"] = mission.output
        log.msg(self.metadata)
        # send the metadata
        log.msg("sending metadata")
        self.fileMap[self.metadata["filename"]] = self.metadata
        #self.sendMetadata(self.metadata)
        utils.saveMetadata(self.metadata, self.metadir)
        task.deferLater(reactor, 1, self.getMission)
        
    def downlinkMissionComplete(self, mission):
        log.msg("Downlink Mission Accomplished")
        self.fileMap[self.metadata["filename"]] = self.metadata
        self.sendMetadata(self.metadata)
        utils.saveMetadata(self.metadata, self.metadir)
        task.deferLater(reactor, 1, self.missionComplete, mission)

    # send a notification that current mission is complete and fetch next    
    def missionComplete(self, mission):
        print("MISSION COMPLETE")
        self.sendData("GET_MISSION:" + mission.tostr())
        self.mission = None
