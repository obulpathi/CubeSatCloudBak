import math
import Image
import logging
import random

from cloud.core.cubesat import CubeSat
from cloud.core.common import *
        
class Master(CubeSat):
    def __init__(self, name, config):
        super(Master, self).__init__(name, config)
        self.status = STARTING
        self.slaves = []
        self.job = None
        self.slave_table = {}
        self.logger = logging.getLogger("Master")
        
    def setServer(self, server):
        self.server = server
    
    def setSlaves(self, slaves):
        self.slaves = slaves
        
    def getServer(self):
        return self.server
    
    def setRelayGroundstation(self, goundstation):
        self.relay_groundstation = groundstation
    
    def getRelayGroundstation(self):
        return self.relay_groundstation
    
    def init(self, graph, nodes):
        super(Master, self).init(graph, nodes)
        # initalize slave table
        for slave in self.slaves:
            self.slave_table[slave] = IDLE
    
    # simulate sensing and return filename containing the remote sensing data
    def sense(self):
        return "image.jpg"
    
    # split the remote sensing data into chunks
    def createChunks(self, filename):
        sensor_data = Image.open(filename)
        width = sensor_data.size[0]
        height = sensor_data.size[1]
        for y in range(0, int(math.ceil(float(height)/chunk_y))):
            for x in range(0, int(math.ceil(float(width)/chunk_x))):
                box = (x * chunk_x, y * chunk_y, (x+1) * chunk_x, (y+1) * chunk_y)
                chunk = sensor_data.crop(box)
                chunk.save("chunks/chunk:" + str(y) + "x" + str(x) + ".jpg")
                    
    def addJob(self, job):
        self.job = job
        self.status = WORKING
    
    # assign new chunk
    def assignNewChunk(self, slave):
        chunk = self.job.chunks[0]
        self.job.chunks.remove(chunk)
        chunk.slave = slave
        self.chunks.append(chunk)
        self.slave_table[slave] = WORKING
        self.logger.debug("Assigning chunk: ID: " + str(chunk.id) + ", Size: " + str(chunk.size) + " to slave: " + slave.name)
        # Packet = Packet(sender, receiver, source, destination, datatype, payload, latency, size)
        sender, receiver, source, destination = self, self.network.nextHop(self, slave), self, slave
        datatype, payload, latency, size = NEW_CHUNK, chunk, CS2CSLink.latency, CS2CSLink.overhead + chunk.size
        packet = Packet(sender, receiver, source, destination, datatype, chunk.id, payload, latency, size)
        self.transmit(packet)

    # remove chunk from scheduled chunks    
    def finishedChunk(self, chunk):
        self.logger.debug("Removing chunk :" + str(chunk))
        self.slave_table[chunk.slave] = IDLE
        self.chunks.remove(chunk)
    
    # processing work
    def process(self):
        self.logger.debug("Status: " + self.status)
        if self.status == STARTING:
            return
        for slave in self.slaves:
            if self.slave_table[slave] == WORKING:
                pass # don't do anything
            elif self.slave_table[slave] == IDLE:
                if not self.job:
                    break
                if not self.job.chunks:
                    break
                self.assignNewChunk(slave)
            elif slave.status == FAILURE:
                slave.reset()
                self.assignNewChunk(slave)
            else:
                # unknown status :(
                slave.status = FAILURE

    # GroundStation -> CubeSat comunication
    def uplinked(self, packet):
        # check from, to and other stuff for the packet
        if packet.datatype == COMMAND_IMAGE_DOWNLINK:
            self.logger.debug("Command: " + str(packet.payload) + " received")
            self.receivedCommand(packet.payload)
        else:
            self.logger.debug("Received unknown packet")
  
    # received something from another CubeSat
    def received(self, packet):
        self.logger.debug("Received packet: " + str(packet))
        # if packet if not for self, relay it to the destination
        if packet.destination != self:
            receiver = network.nextHop(self, packet.destination)
            packet.receiver = receiver
            self.transmit(packet)
        if packet.datatype == FINISHED_CHUNK:
            self.finishedChunk(packet.payload)
        elif packet.datatype == ACK:
            print "###############################################################################"
        else:
            pass
        
    # received a command from Ground Station    
    def receivedCommand(self, job):
        self.job = job
        self.logger.debug("Scheduling command : " + str(job))
        # create chunks
        num_of_chunks = self.job.size / CHUNK_SIZE
        self.logger.debug("Number of Chunks: " + str(num_of_chunks))
        for i in range(num_of_chunks):
            # Gaussian distribution with mu = 0, sig^2 = 0.2
            self.job.chunks.append(Chunk(i, CHUNK_SIZE + CHUNK_VARIATION * random.normalvariate(0, 0.44), None))
        self.logger.debug("Chunks: " + str(self.job.chunks))
        self.status = WORKING
        
    def downlinkResult(self, result):
        # Packet = (sender, receiver, source, destination, datatype, payload, latency, size)
        packet = Packet(self, self.server, self, self.server, RESULT, "RESULT", 10, MB)
        self.downlink(packet)
    
    # do unit of work here
    def step(self):
        # do work: process, store, communicate and consume energy
        self.process()
        self.communicate()
        self.eps()
           
        # if SIMULATION is STARTING, skip checking
        if self.status == STARTING:
            return
        # if SIMULAITION is FINISHED, skip checking
        if self.statuc == FINISHED:
            return
        # check if master has more jobs to schedule
        if not self.job.chunks:
            self.logger.debug("Master has no more jobs to schedule")
        if self.chunks:
            self.logger.debug("Sheduled chunks: " + str(self.chunks))
        # if execution of job is finished, end simulation
        if not self.job.chunks and not self.chunks:
            self.logger.debug("Network is idle")
            self.status = FINISHED
            self.downlinkResult(0)
