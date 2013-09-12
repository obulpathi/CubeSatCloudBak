from cubenet.core.cubesat import CubeSat
from cubenet.core.common import *
import logging
import random
        
class Master(CubeSat):
    def __init__(self, name, config):
        super(Master, self).__init__(name, config)
        self.status = STARTING
        self.slaves = []
        self.job = None
        self.chunks = []
        self.slave_table = {}
        self.logger = logging.getLogger("Master")
        
    def setServer(self, master):
        self.master = master
    
    def setSlaves(self, slaves):
        self.slaves = slaves
        
    def getServer(self):
        return self.master
    
    def setRelayGroundstation(self, goundstation):
        self.relay_groundstation = groundstation
    
    def getRelayGroundstation(self):
        return self.relay_groundstation
    
    def init(self):
        # initalize slave table
        for slave in self.slaves:
            self.slave_table[slave] = IDLE
            
    def addJob(self, job):
        self.job = job
        self.status = WORKING
    
    def assignNewChunk(self, slave):
        # merge both chunks into one ... make it a class ... instead of tuple ... 
        chunk = self.job.chunks[0]
        self.job.chunks.remove(chunk)
        # chunk = Chunk(id, size, slave)
        chunk = Chunk(chunk.id, chunk.size, slave)
        self.logger.debug("Assigning chunk: " + str(chunk) + "to slave: " + slave.name)
        self.chunks.append(chunk)
        self.slave_table[slave] = WORKING
        # Packet = Packet(sender, receiver, source, destination, datatype, payload, latency, size)
        sender, receiver, source, destination = self, self.network.nextHop(self, slave), self, slave
        datatype, payload, latency, size = NEW_CHUNK, chunk, CS2CS_LATENCY, CS2CS_HEADER_SIZE + chunk.size
        packet = Packet(sender, receiver, source, destination, datatype, payload, latency, size)
        self.transmit(packet)
    
    def finishedChunk(self, chunk):
        self.logger.debug("Removing chunk :" + str(chunk))
        self.slave_table[chunk.slave] = IDLE
        self.chunks.remove(chunk)
    
    # processing work
    def process(self):
        self.logger.debug("Status: " + self.status)
        if self.chunks:
            self.logger.debug("Sheduling chunks: " + str(self.chunks))
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
    
    # transmit function
    def transmit(self, packet):
        # transmit to the receiver
        packet.receiver.receive(packet)
        
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
            pass
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
        
    def downlinkResult(self):
        pass
    
    # do unit of work here
    def step(self):
        # do work: process, store, communicate and consume energy
        self.process()
        self.communicate()
        self.eps()
           
        # if SIMULATION is STARTING, skip checking
        if self.status == STARTING:
            return
        # check if master has more jobs to schedule
        if not self.job.chunks:
            self.logger.debug("Master has no more jobs to schedule")
        # if execution of job is finished, end simulation
        if not self.job.chunks and not self.chunks:
            self.logger.debug("Network is idle")
            self.status = FINISHED
