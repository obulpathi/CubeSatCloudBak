import pickle

from twisted.python import log
from twisted.internet import task
from twisted.internet import reactor
from twisted.internet import protocol

from cloud.common import *

class TransportMasterProtocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory
        
    # received data      
    def dataReceived(self, packetstring):
        packet = pickle.loads(packetstring)
        if packet.flags == REGISTER:
            self.registerWorker(packet)
        elif packet.flags == "STATE":
            self.gotState(packet)
        elif packet.flags == "GET_WORK":
            self.sendWork(packet.source)
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
        if self.factory.registrationCount == 1:
            task.deferLater(reactor, 0.1, self.getMission)
    
    # get mission
    def getMission(self):
        packet = Packet(self.factory.address, "Receiver", self.factory.address, "Server", \
                        GET_MISSION, None, HEADERS_SIZE)
        packetstring = pickle.dumps(packet)
        self.transport.write(packetstring)
    
    # got mission
    def gotMission(self, mission):
        self.factory.mission = mission
    
    # send work to workers   
    def sendWork(self, destination):
        if not self.factory.mission:
            packet = Packet(self.factory.address, "Receiver", self.factory.address, destination, \
                            "NO_WORK", None, HEADERS_SIZE)
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

    # received command
    def receivedCommand(self, packet):
        log.msg("Received Command>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        if packet.flags == TORRENT:
            log.msg("Torrent command")
        elif packet.flags == MAPREDUCE:
            log.msg("MapReduce command")
        elif packet.flags == CDFS:
            log.msg("CDFS command")
        else:
            log.msg("Unknown command")


# Master factory
class TransportMasterFactory(protocol.Factory):
    def __init__(self):
        self.status = "START"
        self.address = "Master"
        self.mission = None
        self.registrationCount = 0
        
    def buildProtocol(self, addr):
        log.msg("build protocol called")
        return TransportMasterProtocol(self)
