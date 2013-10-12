import os
import math
import pickle
from time import sleep
from uuid import uuid4
from threading import Lock

from twisted.python import log
from twisted.internet import reactor
from twisted.internet import protocol
from twisted.protocols.basic import LineReceiver

from cloud import utils
from cloud.common import *
from cloud.transport.transport import MyTransport

class TransportServerProtocol(LineReceiver):
    def __init__(self, factory, homedir):
        self.factory = factory
        self.homedir = homedir
        self.name = "Server"
        self.mode = "LINE"
        self.work = None
        self.fragments = None
        self.fragmentsLength = 0
        self.mutexpr = Lock()
        self.mutexsp = Lock()
        self.mytransport = MyTransport(self, self.name)

    def lineReceived(self, line):
        fields = line.split(":")
        self.work = Work(fields[1], fields[2], fields[3], None)
        self.work.size = fields[4]
        self.packetLength = int(self.work.size)
        self.fragments = None
        self.fragmentsLength = 0
        self.mode = "RAW"
        self.setRawMode()

    def rawDataReceived(self, data):
        # buffer the the fragments
        if not self.fragments:
            self.fragments = data
            self.fragmentsLength = len(self.fragments)
        else:
            self.fragments = self.fragments + data
            self.fragmentsLength = self.fragmentsLength + len(data)
        # check if we received all the fragments
        if self.fragmentsLength == self.packetLength:
            self.work.payload = self.fragments
            self.mode = "LINE"
            self.setLineMode()
            self.receivedChunk(self.work)

    """
    def lineReceived(self, line):
        self.mutexpr.acquire()
        print(line)
        fields = line.split(":")
        command = fields[0]
        if command == "CHUNK":
            self.chunk = Chunk(fields[1], fields[3], fields[4], None)
            self.mode = "RAW"
            self.setRawMode()
        elif command == REGISTER:
            if packet.source == "GroundStation":
                self.registerGroundStation(packet)
            else:
                self.registerCubeSat(packet)
        elif command == UNREGISTER:
            self.unregister(packet)
        elif command == GET_MISSION:
            self.getMission(packet.sender)
        elif command == "COMPLETED_MISSION":
            self.factory.finishedMission(packet.payload)
        elif command == "MISSION":
            self.finishedMission(packet.payload)
        else:
            log.msg("Received unkown packet: %s", line)
            print(line)
        self.mutexpr.release()
    
    def rawDataReceived(self, data):
        self.receivedChunk(data)
        self.setLineMode()
    """
    # send a packet, if needed using multiple fragments
    def sendPacket(self, packetstring):
        self.mutexsp.acquire()
        length = len(packetstring)
        packetstring = str(length).zfill(LHSIZE) + packetstring
        for i in range(int(math.ceil(float(length)/MAX_PACKET_SIZE))):
            self.transport.write(packetstring[i*MAX_PACKET_SIZE:(i+1)*MAX_PACKET_SIZE])
        self.mutexsp.release()
            
    # register groundstation
    def registerGroundStation(self, packet):
        log.msg("Registered ground station")
        self.factory.registrationCount = self.factory.registrationCount + 1
        packet = Packet(self.factory.address, "receiver", self.factory.address, self.factory.registrationCount, \
						REGISTERED, self.factory.registrationCount, HEADERS_SIZE)
        packetstring = pickle.dumps(packet)
        log.msg(packet)
        self.sendPacket(packetstring)
    
    # unregister what?
    def unregister(self, packet):
        log.msg("TODO: unregister")
        log.msg(packet)
    
    # register CubeSat
    def registerCubeSat(self, packet):
        log.msg("Registering CubeSat")
        new_packet = Packet(self.factory.address, packet.sender, self.factory.address, packet.source, \
                            REGISTERED, None, HEADERS_SIZE)
        packetstring = pickle.dumps(new_packet)
        log.msg(new_packet)
        self.sendPacket(packetstring)

    # received a chunk
    def receivedChunk(self, work):
        log.msg(work.filename)
        filename = self.homedir + work.filename
        if not os.path.exists(os.path.split(filename)[0]):
            os.mkdir(os.path.split(filename)[0])
        handler = open(filename, "w")
        handler.write(work.payload)
        handler.close()

    def finishedMission(self, mission):
        mission = self.factory.finishedMission(mission)
        packet = Packet(self.factory.address, "Receiver",
                        self.factory.address, "Master",
                        MISSION, mission, HEADERS_SIZE)
        packetstring = pickle.dumps(packet)
        log.msg(packet)
        self.sendPacket(packetstring)
                
    def getMission(self):
        mission = self.factory.getMission()
        data = "MISSION:" + mission.tostr()
        print(data)
        self.sendLine(data)
        
# Server factory
class TransportServerFactory(protocol.Factory):
    def __init__(self, commands, homedir, fromSServerToServer, fromServerToSServer):
        self.address = "Server"
        self.buildMissions(commands)
        self.registrationCount = 100
        self.homedir = os.path.expanduser(homedir)
        self.fileMap = {}
        self.mutex = Lock()
        try:
            os.mkdir(self.homedir)
            os.mkdir(self.homedir + "metadata/")
        except OSError:
            print(self.homedir)
            log.msg("OSError: Unable to create data directories, exiting")
            exit(1)
        self.fromSServerToServer = fromSServerToServer
        self.fromServerToSServer = fromServerToSServer
        self.waiter = WaitForData(self.fromSServerToServer, self.getData)
        self.waiter.start()
       
    def buildProtocol(self, addr):
        return TransportServerProtocol(self, self.homedir)
    
    def getData(self, line):
        #log.msg("Server: Got a packet from SServer")
        # log.msg(line)
        self.lineReceived(line)
        
    def buildMissions(self, commands):
        self.missions = []
        if not commands:
            return
        for command in commands:
            log.msg(command)
            mission = Mission()
            mission.operation = command.operation
            mission.filename = command.filename
            mission.uuid = uuid4()
            if command.operation == SENSE:
                mission.lat = command.lat
                mission.lon = command.lon
            if command.operation == PROCESS:
                mission.output = command.output
            self.missions.append(mission)

    def lineReceived(self, line):
        # print(line)
        fields = line.split(":")
        command = fields[0]
        if command == "GET_MISSION":
            self.sendMission()
        elif command == "METADATA":
            self.receivedMetadata(line[9:])
        elif command == REGISTER:
            if packet.source == "GroundStation":
                self.registerGroundStation(packet)
            else:
                self.registerCubeSat(packet)
        elif command == UNREGISTER:
            self.unregister(packet)
        elif command == GET_MISSION:
            self.getMission(packet.sender)
        elif command == CHUNK or command == "CHUNK":
            self.receivedChunk(packet.payload)
        elif command == "COMPLETED_MISSION":
            self.factory.finishedMission(packet.payload)
        elif command == "MISSION":
            self.finishedMission(packet.payload)
        else:
            log.msg("Received unkown packet: %s", line)
            print(line)
                
    def sendMission(self):
        mission = None
        if not self.missions:
            return None
        if self.missions:
            mission = self.missions[0]
            self.missions = self.missions[1:]
            log.msg("Sending mission: %s" % mission)
            packet = "MISSION:" + mission.tostr()
            self.fromServerToSServer.put(packet)
        else:
            self.fromServerToSServer.put("MISSION:") 
    
    def receivedMetadata(self, metastring):
        # log.msg(metastring)
        metadata = Metadata()
        metadata.fromstr(metastring)
        self.fileMap[metadata.filename] = metadata
        self.finishedDownlinkMission(metadata.filename)

    def finishedMission(self, mission):
        self.mutex.acquire()
        if not mission:
            log.msg("Finished unknown mission")
        elif mission.operation == "SENSE":
            pass
        elif mission.operation == "STORE":
            pass
        elif mission.operation == "PROCESS":
            pass
        elif mission.operation == "DOWNLINK":
            self.finishedDownlinkMission(mission.filename)
        else:
            log.msg("Finished unknown mission: %s", str(mission))
        self.mutex.release()
        return self.getMission()

    def finishedDownlinkMission(self, filename):
        utils.stichChunksIntoImage(self.homedir, self.homedir + filename, self.fileMap[filename]) 
        log.msg("Downlink Mission Complete")
