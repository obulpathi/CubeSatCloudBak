#! /usr/bin/env python

from math import sqrt
import networkx as nx
from common import *
import logging
import threading

from cloud.core.transceiver import Transceiver

class CubeSat(threading.Thread):
    # initializaiton
    def __init__(self, name, config):
        threading.Thread.__init__(self)
        self.name = name
        self.processor = Processor(config.processor)
        self.memory = Memory(config.memory)
        self.battery = Battery(config.battery)
        self.nic = NIC(config.nic)
        self.transciever = Transciever(config.transciever)
        self.location = Location(config.location)
        self.tle = TLE(config.tle)
        self.transceivers = {}
        self.GS2CSQueue = []
        self.CS2GSQueue = []
        self.status = IDLE
        self.logger = logging.getLogger("CubeSat")
    
    # return string representation of node
    def __repr__(self):
        return str(self.name)

    # basic initialization
    def init(self, graph, nodes):
        pass
    
    # set network
    def setNetwork(self, network):
        self.network = network
    
    # CubeSat map function
    def cmap(self, map_task):
        # add the map task to the task list of processor
        self.processor.tasks.append(map_task)
    
    # CubeSat reduce function
    def creduce(self, reduce_task):
        # add the reduce task to the task list of processor
        self.processor.tasks.append(reduce_task)
    
    # do the processing here
    def process(self):
        pass

    # establish link between this cubesat and ground station
    def connect(self, groundstation):
        self.groundstation = groundstation
    
    # close the link between this cubesat and current ground station
    def disconnect(self):
        self.groundstation = None
    
    # handoff to a new ground station
    def handoff(self, new_groundstation):
        self.groundstation = new_groundstation
                       
    # GroundStation -> CubeSat comunication
    def uplink(self, packet):
        # Packet = namedtuple('Packet', 'sender receiver source destination datatype payload latency size')
        delay = ((packet.size * 1000) / GS2CSLink.datarate) + GS2CSLink.latency # delay in ms
        self.GS2CSQueue.append(QItem(packet, delay))
        self.logger.debug("Started receiving packet from GroundStation")

    # GroundStation -> CubeSat comunication
    def uplinked(self, packet):
        # receive packet from
        pass
        
    # CubeSat -> GroundStation comunication
    def downlink(self, packet = None):
        # append packet to Queue
        if packet:
            self.CS2GSQueue.append(packet)
        # if transceiver is busy, return
        if self.transceiver.status != IDLE:
            return 0
        # if transmit Queue is empty, return
        if not self.CS2GSQueue:
            return 0
        # transmit the frist packet in Queue
        self.transceiver.transmit(self.CS2GSQueue[0])
    
    # CubeSat -> GroundStation comunication
    def downlinked(self, packet):
        # remove the packet from CS2GSQueue
        if packet == self.CS2GSQueue[0]:
            self.CS2GSQueue = self.CS2GSQueue[1:]
        
    # CubeSat to CubeSat Communication
    def transmit(self, packet):
        self.transceivers[packet.receiver].transmit(packet)
    
    # start receiving a packet from another CubeSat
    def receive(self, packet):
        pass
    
    # received a packet from another CubeSat
    def received(self, packet):
        pass
        
    # Communicate
    def communicate(self):
        # process Ground Station -> CubeSat queue
        packet = processQueue(self.GS2CSQueue, "GS2CSQueue", self.logger)
        # if any packet is received, process it
        if packet:
            self.uplinked(packet)   
        # step the transcievers
        for transceiver in self.transceivers.itervalues():
            transceiver.step()
            
    # eps subsystem
    def eps(self):
        battery = self.battery
        # charge from solar cells
        if (battery.charge + battery.charge_rate < battery.capacity):
            battery.charge = battery.charge + battery.charge_rate
        else:
            battery.charge = battery.capacity
        # discharge for maintaince
        # battery.charge = battery.charge - self.power.maintainance
    
    # modify this >>>
    # add tasks to the memory subsystem
    def fileops(self, foleop):
        pass
        
    # memory subsystem
    def memory(self):
        pass
    
    # return distance between this node and the other
    def distance(self, other):
        return sqrt((self.location[0] - other.location[0]) ** 2 + (self.location[1] - other.location[1]) ** 2)
    
    # model failures here
    def fail(self):
        # model failures : failure = random(1, 1000000) etc
        # self.state = failed, errorID
        # put a particular component into failure state or link failure
        pass
    
    # do any repaits here
    def repair(self):
        # check if its a temporary failure .. if yes .. fix it else repair with probability :)
        pass

    # do maintainance
    def maintainance(self):
        # fail 
        self.fail()
        
        # repair
        self.repair()
        
    # sleep aka low power mode
    def sleep(self):
        # give sleep indicator to neighbouring nodes
        # set wakeup timer and goto sleep
        pass
	
	# thread run process
	def run(self):
		pass
