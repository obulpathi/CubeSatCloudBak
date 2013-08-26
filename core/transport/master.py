import pickle

from twisted.internet import task
from twisted.internet import reactor
from twisted.internet import protocol

from cloud.core.common import *

class TransportMasterProtocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory
        loopcall2 = task.LoopingCall(self.pollForDataFromCSClient)
        loopcall2.start(0.1) # call every second
        
    def pollForDataFromCSClient(self):
        try:
            packet = self.factory.fromCSClientToWorker.get(False)
            if packet:
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
    def __init__(self, fromWorkerToCSClient, fromCSClientToWorker):
        self.id = 0
        self.registrationCount = 0
        self.fromWorkerToCSClient = fromWorkerToCSClient
        self.fromCSClientToWorker = fromCSClientToWorker
        
    def buildProtocol(self, addr):
        print("build protocol called")
        return TransportMasterProtocol(self)
