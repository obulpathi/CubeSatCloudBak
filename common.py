#!/usr/bin/env python

import threading
from collections import namedtuple

# Packet = (sender, receiver, source, destination, datatype, payload, latency, size)

# global mutex
from threading import Lock
gmutex = Lock()

# GENERAL CONSTANTS
KB = 1024
KBPS = 1024
MB = 1048576
MBPS = 1048576
GB = 1073741824
GHz = 1000000000
MILLION = 1000000
BILLION = 1000000000

MAX_PACKET_SIZE = 10000

# chunk constants
# CHUNK_SIZE = 65536
CHUNK_SIZE = 5000

# commands
ACK = "ACK"
CHUNK = "CHUNK"
NEW_CHUNK = "NEW_CHUNK"
BAD_PACKET = "BAD_PACKET"
LAST_PACKET = "LAST_PACKET"
DUMMY_PAYLOAD = "DUMMY_PAYLOAD"
FINISHED_CHUNK = "FINISHED_CHUNK"

# Link Layer definitions
LL_ACK = "LL_ACK"
LL_END_ACK = "LL_END_ACK"
LL_BAD_PACKET = "LL_BAD_PACKET"
LL_END_PACKET = "LL_END_PACKET"

# FSM States
IDLE     = "IDLE"
STARTING = "STARTING"
WORKING  = "WORKING"
WAITING  = "WAITING"
FAILURE  = "FAILURE"
FINISHED = "FINISHED"
TRANSMIT = "TRANSMIT"
RECEIVE  = "RECEIVE"

# chunk states
UNASSINGED = "UNASSIGNED"

# battery
BATTERY_LOW = 100

# Communication channel models
Link = namedtuple('Link', 'datarate mtu latency overhead')
S2GSLink = Link(10 * MBPS, MB, 100, 64)
GS2SLink = Link(10 * MBPS, MB, 100, 64)
GS2CSLink = Link(9600, MB, 5, 64)
CS2GSLink = Link(9600, MB, 5, 64)
CS2CSLink = Link(MBPS, MB, 2, 64)

# chunk sizes
chunk_x = 200
chunk_y = 200

Box = namedtuple('Box', 'left top right bottom')

class WorkerState(object):
    def __init__(self, address, transport):
        self.address = address
        self.transport = transport
        self.state = "IDLE"
        self.job = None

class Work(object):
    def __init__(self, uuid, job, filename, payload):
        self.uuid = uuid
        self.job = job
        self.filename = filename
        self.payload = payload
        
    def __repr__(self):
        strrepr =  "uuid: " + str(self.uuid) + ", job: " + self.job + ", filename: " + self.filename
        if self.job == "STORE":
            strrepr = strrepr + ", size: " + str(self.size)
        return strrepr
        
    def tostr(self):
        strrepr = str(self.uuid) + ":" + self.job + ":" + self.filename
        if self.payload:
            strrepr = strrepr + ":" + self.payload
        if self.job == "STORE":
            strrepr = strrepr + ":" + str(self.size)
        return strrepr
        
    def fromstr(self, initstr):
        fields = initstr.split(":")
        self.uuid = fields[0]
        self.job = fields[1]
        self.filename = fields[2]
        if self.job == "STORE":
            self.size = fields[3]

class Chunk(object):
    def __init__(self, uuid, name, size, box):
        self.uuid = uuid
        self.name = name
        self.size = size
        self.box = box
        self.status = "UNASSIGNED"
        self.worker = None
    def __repr__(self):
        return "Name: " + str(self.name) + ", Size: " + str(self.size) + \
               ", Box: " + str(self.box) + ", Status: " + str(self.status) + ", Worker: " + str(self.worker)

class CodedChunk(object):
    def __init__(self, uuid, name, size):
        self.uuid = uuid
        self.name = name
        self.size = size
        self.status = "UNASSIGNED"
        self.worker = None
        
    def __repr__(self):
        return "Name: " + str(self.name) + ", Size: " + str(self.size) + \
               ", Status: " + str(self.status) + ", Worker: " + str(self.worker)

# Packet flags
NO_FLAG     = "NO_FLAG"
REGISTER    = "REGISTER"
REGISTERED  = "REGISTERED"
UNREGISTER  = "UNREGISTER"
UNREGISTERED= "UNREGISTERED"
TORRENT     = "TORRENT"
MAPREDUCE   = "MAPREDUCE"
GET_CHUNK   = "GET_CHUNK"
CHUNK       = "CHUNK"
COMMAND     = "COMMAND"
GET_MISSION = "GET_MISSION"
MISSION     = "MISSION"
SENSE       = "SENSE"
STORE       = "STORE"
PROCESS     = "PROCESS"
DOWNLINK    = "DOWNLINK"

# packet constants
HEADERS_SIZE = 22
LHSIZE  = 6

# Packet definition
class Packet(object):
    def __init__(self, sender, receiver, source, destination, flags, payload, size):
        self.sender = sender
        self.receiver = receiver
        self.source = source
        self.destination = destination
        self.payload = payload
        self.size = size
        self.flags = flags
        
    def __repr__(self):
        flagstring = ""
        if self.flags == REGISTER:
            flagstring = flagstring + ", " + "REGISTER"
        elif self.flags == REGISTERED:
            flagstring = flagstring + ", " + "REGISTERED"
        elif self.flags == UNREGISTER:
            flagstring = flagstring + ", " + "UNREGISTER"
        elif self.flags == UNREGISTERED:
            flagstring = flagstring + ", " + "UNREGISTERED"
        elif self.flags == TORRENT:
            flagstring = flagstring + ", " + "TORRENT"
        elif self.flags == MAPREDUCE:
            flagstring = flagstring + ", " + "MAPREDUCE"
        elif self.flags == GET_CHUNK:
            flagstring = flagstring + ", " + "GET_CHUNK"
        elif self.flags == CHUNK:
            flagstring = flagstring + ", " + "CHUNK"
        elif self.flags == "CHUNK":
            flagstring = flagstring + ", " + "CHUNK"
        elif self.flags == MISSION:
            flagstring = ", MISSION"
        else:
            flagstring = ", " + self.flags
        
        return "Sender: " + str(self.sender) + ", Receiver: " + str(self.receiver) + ", Source: " + \
                str(self.source) + ", Destination: " + str(self.destination) + flagstring + \
                ", Payload: " + str(self.payload) + ", Size: " + str(self.size)

class Mission(object):
    def __init__(self):
        pass  
    def __repr__(self):
        """
        if self.operation == SENSE:
            return "Mission: " + self.operation + ", filename: " + self.filename + ", UUID: " + str(self.uuid) + \
                   ", lat: " + self.lat + ", lon: " + self.lon
        else:
        """
        return "Mission: " + self.operation + ", filename: " + self.filename + ", UUID: " + str(self.uuid)
    def tostr(self):
        strrepr = self.operation + ":" + self.filename + ":" + str(self.uuid)
        if self.operation == "PROCESS":
            strrepr = strrepr + ":" + self.output
        return strrepr
    def fromstr(self, line):
        fields = line.split(":")
        self.operation = fields[0]
        self.filename = fields[1]
        self.uuid = fields[2]
        if self.operation == "PROCESSS":
            self.output = fields[3]
                
class WaitForData(threading.Thread):
    def __init__(self, queue, callback):
        self.queue = queue
        self.callback = callback
        threading.Thread.__init__(self)
    def run (self):
        while True:
            data = self.queue.get()
            self.callback(data)

# configuration object
class Struct(object):
    def __init__(self, d):
        for key, value in d.items():
            if isinstance(value, (list, tuple)):
               setattr(self, key, [Struct(item) if isinstance(item, dict) else item for item in value])
            else:
               setattr(self, key, Struct(value) if isinstance(value, dict) else value)
    def __repr__(self):
        return '{%s}' % str(', '.join('%s : %s' % (key, repr(value)) for (key, value) in self.__dict__.iteritems()))

class Metadata(object):
    def __init__(self):
        pass

    # save the metadata into file
    def save(self, directory):
        # reconstruct the whole file path
        filename = directory + self.filename.split(".")[0]
        print("Saving metadata for the file: %s" % filename)
        metafile = open(filename, "w")
        metastring = self.tostr()
        metafile.write(metastring)
        metafile.close()
    
    def __repr__(self):
        data = self.filename
        data = data +  "\n" + str(self.height)
        data = data + "\n" + str(self.width)
        data = data + "\n" + self.directory
        chunkMap = self.chunkMap
        numOfWorkers = len(chunkMap)
        data = data +  "\n" + str(numOfWorkers)
        for worker, chunklist in chunkMap.iteritems():
            data = data +  "\n" + str(worker)
            for chunk in chunklist:
                data = data +  ":" + chunk.uuid
                data = data +  ":" + chunk.name
                data = data +  ":" + str(chunk.size)
                data = data +  ":" + str(chunk.box)
                data = data +  ":" + str(chunk.box) + "\n"
        return data

    def tostr(self):
        data = self.filename
        data = data +  ":" + str(self.height)
        data = data + ":" + str(self.width)
        data = data + ":" + self.directory
        chunkMap = self.chunkMap
        numOfWorkers = len(chunkMap)
        data = data +  ":" + str(numOfWorkers)
        for worker, chunklist in chunkMap.iteritems():
            data = data +  ":" + str(worker)
            numOfChunks = len(chunklist)
            data = data +  ":" + str(numOfChunks)
            for chunk in chunklist:
                data = data +  ":" + chunk.uuid
                data = data +  ":" + chunk.name
                data = data +  ":" + str(chunk.size)
                data = data +  ":" + str(chunk.box.left)
                data = data +  ":" + str(chunk.box.top)
                data = data +  ":" + str(chunk.box.right)
                data = data +  ":" + str(chunk.box.bottom)
        return data

    def fromstr(self, metadata):
        fields = metadata.split(":")
        self.filename = fields[0]
        self.height = int(fields[1])
        self.width = int(fields[2])
        self.directory = fields[3]
        self.chunkMap = {}
        numOfWorkers = int(fields[4])
        fields = fields[5:]
        for count in range(numOfWorkers):
            worker = fields[0]
            numOfChunks = int(fields[1])
            self.chunkMap[worker] = []
            fields = fields[2:]
            for chunkcount in range(numOfChunks):
                box = Box(int(fields[3]), int(fields[4]), int(fields[5]), int(fields[6]))
                chunk = Chunk(fields[0], fields[1], int(fields[2]), box)
                fields = fields[7:]
                self.chunkMap[worker].append(chunk)

class CCMetadata(object):
    def __init__(self):
        pass

    # save the metadata into file
    def save(self, directory):
        # reconstruct the whole file path
        filename = directory + self.filename.split(".")[0]
        print("Saving metadata for the file: %s" % filename)
        metafile = open(filename, "w")
        metastring = self.tostr()
        metafile.write(metastring)
        metafile.close()
    
    def __repr__(self):
        data = self.filename
        data = data + "\n" + self.directory
        data = data + "\n" + str(self.size)
        chunkMap = self.chunkMap
        numOfWorkers = len(chunkMap)
        data = data +  "\n" + str(numOfWorkers)
        for worker, chunklist in chunkMap.iteritems():
            data = data +  "\n" + str(worker)
            for chunk in chunklist:
                data = data +  ":" + chunk.uuid
                data = data +  ":" + chunk.name
                data = data +  ":" + str(chunk.size) + "\n"
        return data

    def tostr(self):
        data = self.filename
        data = data + ":" + self.directory
        data = data + ":" + str(self.size)
        chunkMap = self.chunkMap
        numOfWorkers = len(chunkMap)
        data = data +  ":" + str(numOfWorkers)
        for worker, chunklist in chunkMap.iteritems():
            data = data +  ":" + str(worker)
            numOfChunks = len(chunklist)
            data = data +  ":" + str(numOfChunks)
            for chunk in chunklist:
                data = data +  ":" + chunk.uuid
                data = data +  ":" + chunk.name
                data = data +  ":" + str(chunk.size)
        return data

    def fromstr(self, metadata):
        fields = metadata.split(":")
        self.filename = fields[0]
        self.directory = fields[1]
        self.size = int(fields[2])
        self.chunkMap = {}
        numOfWorkers = int(fields[3])
        fields = fields[4:]
        for count in range(numOfWorkers):
            worker = fields[0]
            numOfChunks = int(fields[1])
            self.chunkMap[worker] = []
            fields = fields[2:]
            for chunkcount in range(numOfChunks):
                chunk = CodedChunk(fields[0], fields[1], int(fields[2]))
                fields = fields[3:]
                self.chunkMap[worker].append(chunk)

LOREMIPSUM = ":LOREMIPSUM:Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur."
