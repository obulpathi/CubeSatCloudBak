#!/usr/bin/env python

from groundstation import GroundStation
from common import *
import logging

class Server(GroundStation):
    def __init__(self, name):
        self.name = name
        self.master = None
        self.relay_groundstation = None
        self.job = None
        self.state = IDLE
        self.events = []
        self.GS2SQueue = []
        self.logger = logging.getLogger("Server")
    
    def init(self):
        pass
                    
    def setMaster(self, master):
        self.master = master
    
    def getMaster(self):
        self.master = None
        
    def setRelayGroundstation(self, groundstation):
        self.relay_groundstation = groundstation
    
    def getRelayGroundstaiton(self):
        return self.relay_groundstation
    
    def setNetwork(self, network):
        self.network = network
            
    def addJob(self, job):
        self.job = job
        self.logger.debug("Job received by Server: " + str(self.job))
        self.logger.debug("Transmitting Job: " + str(self.job) + " to relay Ground Station")
        self.transmit(job)
        self.job = None
    
    # transmit data to relay ground station
    def transmit(self, data):
        packet = Packet(sender = self, receiver = self.relay_groundstation, source = self, destination = self.master, 
                        datatype = COMMAND_IMAGE_DOWNLINK, id = 0, payload = data, size = 250)
        self.relay_groundstation.receive(packet)
    
    # receive data from ground station
    def receive(self, packet):
        self.logger.debug("Started receiving packet from Ground Station")
        # calculate the delay incurred for this packet
        latency = ((packet.size * 1000) / GS2SLink.datarate) + GS2SLink.latency
        self.logger.debug("Appending packet: " + str(packet) + " Latency: " + str(latency))
        self.GS2SQueue.append(QItem(packet, latency))
    
    # received data from ground station
    def received(self, packet):
        """
        initialize the number of packets et to receive ... 
        wait for all the packets to be received ... 
        once received ... kevv keka ... 
        """
        print "Received a packet: " + str(packet)
        exit()
        """
        log the packets into rcvdQueue
        if all packets received ... self.status = FINISHED
        end simulation ... 
        """
    
    # communicate
    def communicate(self):
        # Ground Station -> Server Queue
        packet = processQueue(self.GS2SQueue, "GS2SQueue", self.logger)
        if packet:
            self.received(packet)
    
    # process
    def process(self):
        pass
    
    # do work: communicate, process
    def step(self):
        self.communicate()
        self.process()
