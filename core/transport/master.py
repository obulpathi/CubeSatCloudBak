import pickle

from twisted.internet import reactor
from twisted.internet import protocol

from cloud.core.common import *

class TransportMasterProtocol(protocol.Protocol):    
    def __init__(self, factory):
        self.factory = factory
        loopcall = task.LoopingCall(self.pollForDataFromCSClient)
        loopcall.start(0.1) # call every second

    def pollForDataFromCSClient(self):
        try:
            print("waiting for data******************************")
            packet = self.factory.fromCSClientToMaster.get(False)
            print("polling for data")
            if packet:
                print("Master received data from CSClient ##########################")
                self.receivedCommand(packet)
        except Exception:
            pass
                
    # received data              
    def dataReceived(self, packetstring):
        packet = pickle.loads(packetstring)
        if packet.flags & REGISTER:
            self.registerWorker(packet)
        elif packet.flags & GET_CHUNK:
            self.transmitChunk(packet.source)
        else:
            log("Unknown stuff")
    
    # register worker
    def registerWorker(self, packet):
        print("registered slave")
        self.factory.registrationCount = self.factory.registrationCount + 1
        packet = Packet(self.factory.id, "receiver", self.factory.id, self.factory.registrationCount, REGISTERED, \
                        self.factory.registrationCount, HEADERS_SIZE)
        packetstring = pickle.dumps(packet)
        self.transport.write(packetstring)
    
    # transmit chunk
    def transmitChunk(self, destination):
        print("Master got request for chunk")
        image = open("chunk.jpg", "rb")
        data = image.read()
        chunk = Chunk("chunkid", "size", "box", data)
        packet = Packet(self.factory.id, "receiver", self.factory.id, destination, CHUNK, \
                        chunk, HEADERS_SIZE)
        packetstring = pickle.dumps(packet)
        self.transport.write(packetstring)

    # received command
    def receivedCommand(self, packet):
        print("Received Command>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        if packet.flags == TORRENT:
            print("Torrent command")
        elif packet.flags == MAPREDUCE:
            print("MapReduce command")
        elif packet.flags == CDFS:
            print("CDFS command")
        else:
            print("Unknown command")


# Master factory
class TransportMasterFactory(protocol.Factory):
    def __init__(self, fromMasterToCSClient, fromCSClientToMaster):
        self.id = 0
        self.registrationCount = 0
        self.fromMasterToCSClient = fromMasterToCSClient
        self.fromCSClientToMaster = fromCSClientToMaster
        
    def buildProtocol(self, addr):
        return TransportMasterProtocol(self)
