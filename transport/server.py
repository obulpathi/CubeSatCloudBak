import os
import math
import pickle
from time import sleep
from uuid import uuid4

from twisted.python import log
from twisted.internet import reactor
from twisted.internet import protocol

from cloud import utils
from cloud.common import *
from cloud.transport.transport import MyTransport

class TransportServerProtocol(protocol.Protocol):
    def __init__(self, factory, homedir):
        self.factory = factory
        self.homedir = homedir
        self.name = "Server"
        self.mytransport = MyTransport(self.name)
        self.fragments = ""
        self.fragmentlength = 0
        self.packetlength = 0

    # received data
    def dataReceived(self, fragment):
        packet = self.mytransport.dataReceived(fragment)
        if packet:
            self.packetReceived(packet)

    # received a packet
    def packetReceived(self, packet):
        log.msg(packet)
        if packet.flags == REGISTER:
            if packet.source == "GroundStation":
                self.registerGroundStation(packet)
            else:
                self.registerCubeSat(packet)
        elif packet.flags == UNREGISTER:
            self.unregister(packet)
        elif packet.flags == GET_MISSION:
            self.getMission(packet.sender)
        elif packet.flags == CHUNK or packet.flags == "CHUNK":
            self.receivedChunk(packet.payload)
        elif packet.flags == "METADATA":
            self.factory.receivedMetadata(packet.payload)
        elif packet.flags == "COMPLETED_MISSION":
            self.factory.finishedMission(packet.payload)
        else:
            log.msg("Received unkown packet: %s", str(packet))
    
    # send a packet, if needed using multiple fragments
    def sendPacket(self, packetstring):
        length = len(packetstring) + 6
        packetstring = str(length).zfill(6) + packetstring
        for i in range(int(math.ceil(float(length)/MAX_PACKET_SIZE))):
            self.transport.write(packetstring[i*MAX_PACKET_SIZE:(i+1)*MAX_PACKET_SIZE])
            
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

    # get mission to ground station
    def getMission(self, receiver):
        mission = self.factory.getMission()
        packet = Packet(self.factory.address, receiver, self.factory.address, "Master", \
                        MISSION, mission, HEADERS_SIZE)
        packetstring = pickle.dumps(packet)
        log.msg(packet)
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

# Server factory
class TransportServerFactory(protocol.Factory):
    def __init__(self, commands, homedir):
        self.address = "Server"
        self.buildMissions(commands)
        self.registrationCount = 100
        self.homedir = homedir
        self.fileMap = {}
        try:
            os.mkdir(homedir)
            os.mkdir(homedir + "metadata/")
        except OSError:
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

    def finishedDownlinkMission(self, filename):
        log.msg("Finished downlink mission ###########################################################")
        log.msg(self.homedir)
        log.msg(filename)
        sleep(10)
        utils.stichChunksIntoImage(self.homedir, self.homedir + filename, self.fileMap[filename]) 
        log.msg("Downlink Mission Complete")
