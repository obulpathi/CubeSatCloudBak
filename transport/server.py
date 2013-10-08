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
        self.mutexpr = Lock()
        self.mutexsp = Lock()
        self.mytransport = MyTransport(self, self.name)

    def lineReceived(self, line):
        self.mutexpr.acquire()
        print(line)
        fields = line.split(":")
        command = fields[0]
        if command == "GET_MISSION":
            self.getMission()
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
        elif command == "METADATA":
            pass
            #self.factory.receivedMetadata(packet.payload)
        elif command == "COMPLETED_MISSION":
            self.factory.finishedMission(packet.payload)
        elif command == "MISSION":
            self.finishedMission(packet.payload)
        else:
            log.msg("Received unkown packet: %s", line)
            print(line)
            utils.banner("LINE")
        self.mutexpr.release()
        
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
    def receivedChunk(self, chunk):
        log.msg(chunk.filename)
        filename = self.homedir + chunk.filename
        if not os.path.exists(os.path.split(filename)[0]):
            os.mkdir(os.path.split(filename)[0])
        handler = open(filename, "w")
        handler.write(chunk.payload)
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
        print("IN GET_MISSION ############################")
        mission = self.factory.getMission()
        data = "MISSION:" + mission.tostr()
        print(data)
        self.sendLine(data)
        """
        packet = Packet(self.factory.address, receiver, self.factory.address, "Master", \
                        MISSION, mission, HEADERS_SIZE)
        packetstring = pickle.dumps(packet)
        log.msg(packet)
        self.sendPacket(packetstring)
        """
        
# Server factory
class TransportServerFactory(protocol.Factory):
    def __init__(self, commands, homedir):
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
       
    def buildProtocol(self, addr):
        return TransportServerProtocol(self, self.homedir)
    
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
        
    def getMission(self):
        mission = None
        if not self.missions:
            return None
        if self.missions:
            mission = self.missions[0]
            self.missions = self.missions[1:]
            log.msg("Sending mission: %s" % mission)
        return mission
    
    def receivedMetadata(self, metadata):
        log.msg("Received metadata")
        log.msg(metadata)
        self.fileMap[metadata["filename"]] = metadata

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
