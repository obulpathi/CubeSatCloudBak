from cloud.core.cubesat import CubeSat
from cloud.core.common import *
import random
import logging

class Slave(CubeSat):
    def __init__(self, name, config):
        super(Slave, self).__init__(name, config)
        self.chunk = None
        self.image = 0
        self.logger = logging.getLogger(self.name)
    
    def setMaster(self, master):
        self.master = master

    # start CubeSat Client
    def startCubeSatClient(self):
        reactor.connectTCP("localhost", 8000, CubeSatClientFactory())
        reactor.run()
        
    # process the chunks assigned by master
    def process(self):
        if self.status == IDLE:
            return
        if self.status == WAITING:
            self.logger.debug("Status: \t" + self.status)
            return
        self.logger.debug("Status: " + str(self.chunk) + ", " + str(self.image))
        if self.image > 0:
            self.image = self.image - KB * (1 - 0.2 * random.normalvariate(0, 0.44))
        else:
            self.status = IDLE
            # send packet to master indicating the sucessful finish of job
            # Packet = namedtuple('Packet', 'sender receiver source destination datatype id payload size')
            receiver = self.network.nextHop(self, self.master)
            packet = Packet(self, receiver, self, self.master, "FINISHED_CHUNK", self.chunk.id, self.chunk, 250)
            self.transmit(packet)

    # start receiving new packet    
    def receive(self, packet):
        super(Slave, self).receive(packet)
    
    # received a packet from another CubeSat
    def received(self, packet):
        if packet.destination != self:
            receiver = self.network.nextHop(self, packet.destination)
            packet.sender = self
            packet.receiver = receiver
            self.transmit(packet)
        elif packet.datatype == NEW_CHUNK:
            self.receivedNewChunk(packet.payload)
        elif packet.datatype == ACK:
            pass
        else:
            self.logger.debug("############################################################################################")
            self.logger.debug("Received a new packet: " + str(packet.datatype))
        
    # received new chunk from master
    def receivedNewChunk(self, chunk):
        self.logger.debug("New chunk received by slave: " + self.name)
        self.chunk = chunk
        self.image = chunk.size
        self.status = WORKING
        
    # do work: process, store, communicate and consume energy
    def step(self):
        self.process()
        self.communicate()
        self.eps()

        # maintainance tasks
        self.maintainance()
        
        # if battery is critically low, go into sleep mode
        if (self.battery.charge < BATTERY_LOW):
            sleep()
    
    # run
    def run(self):
        print(self)
