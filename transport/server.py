import os
import pickle
from time import sleep
from uuid import uuid4

from twisted.python import log
from twisted.internet import reactor
from twisted.internet import protocol

from cloud import utils
from cloud.common import *

class TransportServerProtocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory
        self.filepath = "/home/obulpathi/phd/cloud/data/server/image"
        
    # received data                        
    def dataReceived(self, packetstring):
        packet = pickle.loads(packetstring)
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
        else:
            log.msg("Unknown stuff >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>...")
            log.msg(packet)
    
    # register groundstation
    def registerGroundStation(self, packet):
        log.msg("registered ground station")
        self.factory.registrationCount = self.factory.registrationCount + 1
        packet = Packet(self.factory.address, "receiver", self.factory.address, self.factory.registrationCount, REGISTERED, \
                        self.factory.registrationCount, HEADERS_SIZE)
        packetstring = pickle.dumps(packet)
        self.transport.write(packetstring)
    
    # unregister what?
    def unregister(self, packet):
        log.msg("TODO: unregistered WHAT?? ^&%&^#%@&^#%@#&^ >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    
    # register CubeSat
    def registerCubeSat(self, packet):
        log.msg("registering CubeSat")
        new_packet = Packet(self.factory.address, packet.sender, self.factory.address, packet.source, REGISTERED, \
                        None, HEADERS_SIZE)
        packetstring = pickle.dumps(new_packet)
        self.transport.write(packetstring)

    # get mission to ground station
    def getMission(self, receiver):
        mission = self.factory.getMission()
        packet = Packet(self.factory.address, receiver, self.factory.address, "Master", MISSION, \
            mission, HEADERS_SIZE)
        packetstring = pickle.dumps(packet)
        self.transport.write(packetstring)

    def receivedChunk(self, work):
        log.msg("Received chunk")
        filename = self.filepath + work.filename
        log.msg(filename)
        chunk = open(filename, "w")
        chunk.write(work.payload)
        chunk.close()
        
# Server factory
class TransportServerFactory(protocol.Factory):
    def __init__(self, commands):
        self.address = "Server"
        self.buildMissions(commands)
        self.registrationCount = 100
        self.filepath = "/home/obulpathi/phd/cloud/data/server/"
        try:
            os.mkdir("/home/obulpathi/phd/cloud/data/server")
            os.mkdir("/home/obulpathi/phd/cloud/data/server/image")
            os.mkdir("/home/obulpathi/phd/cloud/data/server/metadata")
        except OSError:
            pass
       
    def buildProtocol(self, addr):
        return TransportServerProtocol(self)
    
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
            self.missions.append(mission)
        
    def getMission(self):
        mission = None
        if not self.missions:
            return None
            # self.finishedDownlinking() >>>>>>>>>>>>>>>>>>>>>>>>>> FIX_THIS
        if self.missions:
            mission = self.missions[0]
            self.missions = self.missions[1:]
            log.msg("Sending mission: %s" % mission)
        return mission
    
    def receivedMetadata(self, metadata):
        log.msg("Received metadata")
        self.metadata = metadata
        print(metadata)
    
    def finishedDownlinking(self):
        filename = "/home/obulpathi/phd/cloud/data/server/image.jpg"
        directory = "/home/obulpathi/phd/cloud/data/server/"
        utils.stichChunksIntoImage(directory, filename, self.metadata) 
        log.msg("Mission Complete")
