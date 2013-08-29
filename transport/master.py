import pickle

from twisted.python import log
from twisted.internet import task
from twisted.internet import reactor
from twisted.internet import protocol

from cloud.common import *

# split the remote sensing data into chunks
def splitImageIntoChunks(self, filename):
    sensor_data = Image.open(filename)
    width = sensor_data.size[0]
    height = sensor_data.size[1]
    for y in range(0, int(math.ceil(float(height)/chunk_y))):
        for x in range(0, int(math.ceil(float(width)/chunk_x))):
            left = x * chunk_x
            top = y * chunk_y
            right = min((x+1) * chunk_x, width)
            bottom = min((y+1) * chunk_y, height)
            box = (left, top, right, bottom)
            chunk = sensor_data.crop(box)
            filename = "chunks/chunk:" + str(y) + "x" + str(x) + ".jpg"
            chunk.save(filename)
            chunkid = str(uuid.uuid4())
            size = os.stat(filename).st_size
            self.chunks.append(Chunk(chunkid, filename, size, box))
            print self.chunks[-1]
            
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
        
    # send work to workers   
    def sendWork(self, destination):
        if not self.factory.mission:
            packet = Packet(self.factory.address, "Receiver", self.factory.address, destination, \
                            "NO_WORK", None, HEADERS_SIZE)
            packetstring = pickle.dumps(packet)
            self.transport.write(packetstring)
        else:
            log.msg("HAS work ... >>>>>>>>>>>>>>>>>>>>. ")
        
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
        self.files = None
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
            self.mission = mission
            self.execute(mission)
        else:
            task.deferLater(reactor, 1, self.getMission)

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
        source = open("sensor_data.jpg", "r")
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
        log.msg(mission)
        log.msg("split the file into chunks and create metadata for this file in files data structure")
        self.getMission()
    
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
