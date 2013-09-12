#!/usr/bin/env python

import logging
from cubenet.core.common import *

class GroundStation(object):
    def __init__(self, name):
        self.name = name
        self.cubesat = None
        self.logger = logging.getLogger("GroundStation")
        self.S2GSQueue = []
        self.CS2GSQueue = []
        global time

    def init(self):
        pass
                
    def connect(self, cubesat):
        self.cubesat = cubesat
    
    def disconnect(self):
        self.cubesat = None

    def setNetwork(self, network):
        self.network = network
        
    def receive(self, packet):
        if not self.cubesat:
            # throw error
            self.logger.debug("GroundStation is not associated with any cubesat")
            return 1
        if packet.destination != self.cubesat:
            # throw error
            self.logger.debug("ERROR: Groundstation associated CubeSat is not packet destination")
            return 2
        
        self.logger.debug("Started receiving packet from Server")
        # calculate the delay incurred for this packet
        latency = ((packet.size * 1000) / S2GSLink.datarate) + S2GSLink.latency
        self.logger.debug("Appending packet: " + str(packet) + " Latency: " + str(latency))
        self.S2GSQueue.append(QItem(packet, latency))
            
    def received(self, packet):
        # if packet is from Server, send it to CubeSat
        self.uplink(packet)
    
    def transmit(self):
        pass
        
    # uplink the packet to CubeSat
    def uplink(self, packet):
        self.logger.debug("Uplinking command: " + str(packet.payload) + " from relay GroundStation to Master CubeSat")
        self.cubesat.uplink(packet)
    
    # downlink the data from CubeSat
    def downlinkData(self):
        pass
    
    # communicate
    def communicate(self):
        # Server -> Ground Station Queue
        packet = processQueue(self.S2GSQueue, "S2GSQueue", self.logger)
        if packet:
            self.received(packet)
        # CubeSat -> Ground Station Queue
    
    # process
    def process(self):
        pass
        
    def step(self):
        self.communicate()
        self.process()
