#!/usr/bin/env python

from collections import namedtuple

# formats
# Chunk = (ID, CHUNK_SIZE, CubeSat)
# Packet = (sender, receiver, source, destination, datatype, payload, latency, size)

# GENERAL CONSTANTS
KB = 1024
KBPS = 1024
MB = 1048576
MBPS = 1048576
GB = 1073741824
GHz = 1000000000
MILLION = 1000000
BILLION = 1000000000

# chunk constants
CHUNK_SIZE = 65536
CHUNK_VARIATION = 16384

# commands
ACK = "ACK"
CHUNK = "CHUNK"
NEW_CHUNK = "NEW_CHUNK"
BAD_PACKET = "BAD_PACKET"
LAST_PACKET = "LAST_PACKET"
DUMMY_PAYLOAD = "DUMMY_PAYLOAD"
FINISHED_CHUNK = "FINISHED_CHUNK"
COMMAND_IMAGE_DOWNLINK = "COMMAND_IMAGE_DOWNLINK"
COMMAND_IMAGE_PROCESS_DOWNLINK = "COMMAND_IMAGE_PROCESS_DOWNLINK"

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

# battery
BATTERY_LOW = 100

# Communication channel models
Link = namedtuple('Link', 'datarate mtu latency overhead')
S2GSLink = Link(10 * MBPS, MB, 100, 64)
GS2SLink = Link(10 * MBPS, MB, 100, 64)
GS2CSLink = Link(9600, MB, 5, 64)
CS2GSLink = Link(9600, MB, 5, 64)
CS2CSLink = Link(MBPS, MB, 2, 64)

# tasks, fileops, ... 
Task = namedtuple('Task', 'ID flops')
Fileops = namedtuple('Fileops', 'ID filename mode data')
Configuration = namedtuple('Configuration', 'processor memory battery nic transciever power location tle')

# mission commands
Torrent = namedtuple('Torrent', 'payload size chunks')
MapReduce = namedtuple('MapReduce', 'payload size chunks')

# subsystems
Power = namedtuple('Power', 'processor memory nic transciever eps maintainance')

class Chunk(object):
    def __init__(self, id, size, slave):
        self.id = id
        self.size = size
        self.slave = slave
    def __repr__(self):
        return "ID: " + str(self.id) + ", Size: " + str(self.size) + ", Slave: " + str(self.slave)
        
class Packet(object):
    def __init__(self, sender, receiver, source, destination, datatype, id, payload, size, flags = None):
        self.sender = sender
        self.receiver = receiver
        self.source = source
        self.destination = destination
        self.datatype = datatype
        self.id = id
        self.payload = payload
        self.size = size
        self.flags = flags
        
    def __repr__(self):
        return "Sender: " + str(self.sender.name) + ", Receiver: " + str(self.receiver.name) + ", Source: " + \
                str(self.source.name) + ", Destination: " + str(self.destination.name) + ", Datatype: " + \
                str(self.datatype) + ", ID: " + str(self.id) + ", Payload: " + str(self.payload) + ", Size: " + str(self.size)

class LLPacket(object):
    def __init__(self, id, size, payload, flags = 0x00):
        self.id = id
        self.size = size
        self.payload = payload
        self.flags = flags
        
    def __repr__(self):
        return "ID: " + str(self.id) + ", Size: " + str(self.size) + ", Payload: " + str(self.payload) + ", Flags: " + str(self.flags)

class Processor(object):
	def __init__(self, config):
		self.clock = config.clock
		self.power = config.power
		self.tasks = []

class NIC(object):
	def __init__(self, config):
		self.bandwidth = config.bandwidth
		self.transmit_queues = []
		self.rxPacket = []

class Memory(object):
	def __init__(self, config):
		self.size = config.size
		self.bandwidth = config.bandwidth
		self.tasks = []

class Transciever(object):
	def __init__(self, config):
		pass

class Battery(object):
	def __init__(self, config):
		self.capacity = config.capacity
		self.charge = config.charge
		self.charge_rate = config.charge_rate
		self.max_current = config.max_current

class Location(object):
	def __init__(self, config):
		pass

class TLE(object):
	def __init__(self, config):
		pass
		
# Queue constructs
class QItem(object):
    def __init__(self, item, timer):
        self.item = item
        self.timer = timer
    def __repr__(self):
       return "Item: " + str(self.item) + "Timer: " + str(self.timer) 
        
def processQueue(queue, qname, logger):
    if queue:
        logger.debug(qname + " status: Item: " + str(queue[0].item) + " Timer: " + str(queue[0].timer))
        queue[0].timer = queue[0].timer - 1
        if queue[0].timer <= 0:
            element = queue[0]
            queue.remove(element)
            return element.item

# configuration
class Struct(object):
    def __init__(self, d):
        for key, value in d.items():
            if isinstance(value, (list, tuple)):
               setattr(self, key, [Struct(item) if isinstance(item, dict) else item for item in value])
            else:
               setattr(self, key, Struct(value) if isinstance(value, dict) else value)
    def __repr__(self):
        return '{%s}' % str(', '.join('%s : %s' % (key, repr(value)) for (key, value) in self.__dict__.iteritems()))
