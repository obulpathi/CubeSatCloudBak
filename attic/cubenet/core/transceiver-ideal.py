import logging
from math import ceil
from random import randint
from cubenet.core.common import *

class Transceiver(object):
    def __init__(self, receiveHandler = None, other = None, logname = None, link = None):
        self.state = IDLE
        self.rxQueue = []
        self.rxedQueue = []
        self.txQueue = []
        self.txBuffer = []
        self.pktCount = 0
        self.other = other
        self.logger = logging.getLogger(logname)
        self.link = link
        self.receiveHandler = receiveHandler
    
    def setOther(self, other):
        self.other = other
    
    def setLogger(self, logname):
        self.logger = logging.getLogger(logname)
        
    # transmit a packet    
    def transmit(self, packet):
        if packet.flags == LL_ACK or packet.flags == LL_END_ACK:
            self.other.receive(packet)
            return
        # if there are packets in transmit queue
        if self.txQueue:
            self.txBuffer.append(packet)
            return
        if isinstance(packet, LLPacket):
            self.other.receive(packet)
            return          
        # calculate the number of small packets
        count = int(ceil(packet.size * 1.0 /self.link.mtu)) - 1
        # split the large packet into small packets and put them into txQueue
        for i in range(count):
            self.txQueue.append(LLPacket(i, self.link.mtu, packet))
        self.txQueue.append(LLPacket(count, packet.size - self.link.mtu * count, packet, LL_END_PACKET)) # last packet
        # transmit the llpackets
        for llpacket in self.txQueue:
            self.other.receive(llpacket)
    
    # retransmit until all packets are delivered to destination
    def retransmit(self):
        # transmit the llpackets
        for llpacket in self.txQueue:
            self.logger.debug("Retransmitting: " + str(llpacket))
            self.other.receive(llpacket)
        
    def receive(self, llpacket):
        # log that CubeSat started receiving llpacket
        self.logger.debug("Started receiving llpacket: " + str(llpacket))
        # add the subpacket to receive queue
        delay = ((llpacket.size * 1000) / self.link.datarate) + self.link.latency
        self.logger.debug("Appending packet: " + str(llpacket) + " Delay: " + str(delay) + " to receive rxQueue")
        self.rxQueue.append(QItem(llpacket, delay))
            
    # received a llpacket
    def received(self, llpacket):
        if llpacket.flags == LL_ACK: # if we received an ACK, remove corresponding packet from txQueue
            for packet in self.txQueue:
                if llpacket.id == packet.id:
                    self.txQueue.remove(packet)
                    return
        if llpacket.flags == LL_END_ACK: #if we received end ack
            for packet in self.txQueue:
                if llpacket.id == packet.id:
                    self.txQueue.remove(packet)
                    if self.txQueue:
                        self.retransmit()
                    else:
                        self.receivedAllAcks()
                    return
        # add the packet to received queue
        self.rxedQueue.append(llpacket)
        # if this the last packet, send ack for the last packet
        if llpacket.flags == LL_END_PACKET:
            self.pktCount = llpacket.id + 1
            self.transmit(LLPacket(llpacket.id, llpacket.size, DUMMY_PAYLOAD, LL_END_ACK))
            # if all llpackets are received
            if len(self.rxedQueue) == self.pktCount:
                self.receivedAllPackets()
        else: # return normal Ack for this llpacket
            self.transmit(LLPacket(llpacket.id, llpacket.size, llpacket, LL_ACK))
    
    # if we sucessfully transmitted all packets
    def receivedAllAcks(self):
        # check transmit buffer to see if there are any pedning packets
        if self.txBuffer:
            packet = self.txBuffer[0]
            self.txBuffer = self.txBuffer[1:]
            self.transmit(packet)
        
    # if we received all packets
    def receivedAllPackets(self):
        packet = self.bundleLLPackets(self.rxedQueue)
        self.rxedQueue = []
        self.receiveHandler(packet)
        
    # bundle LLPackets into NLPacket
    def bundleLLPackets(self, queue):
        payload = queue[0].payload
        packet = Packet(payload.sender, payload.receiver, payload.source, payload.destination, 
                        payload.datatype, payload.id, payload.payload, 0)
        for llpacket in queue:
            packet.size = packet.size + llpacket.size
        return packet      
        
    def step(self):
        # transmit
        if self.txBuffer:
            packet = self.txBuffer[0]
            self.txBuffer = self.txBuffer[1:]
            self.transmit(packet)
        # process CubeSat -> CubeSat queue
        subpacket = processQueue(self.rxQueue, "rxQueue", self.logger)
        if subpacket:
            self.received(subpacket)
            # bad packets ...
            # if timeout || LAST PACKET:
            #   if packets:
            #       retransmit the remaining packets :)
            #   else:
            #       finish :D

if __name__ == "__main__":
    logging.basicConfig(filename = "transceiver.log", level = logging.DEBUG)
    finished = False
    
    def receiveHandler(packet):
        global finished
        finished = True
        print packet
    
    class Cube(object):
        def __init__(self, name):
            self.name = name
            
    x = Transceiver(receiveHandler, None, "X", CS2CSLink)
    y = Transceiver(receiveHandler, None, "Y", CS2CSLink)
    x.other = y
    y.other = x
    
    # Packet(sender, receiver, source, destination, datatype, payload, latency, size)
    packet = Packet(Cube("Sender"), Cube("Receiver"), Cube("Source"), Cube("Destination"), "DATA", "payload", 100, 64* MB + 124312)
    x.transmit(packet)
    time = 0
    while not finished:
        #print x.txQueue, y.txQueue
        x.step()
        y.step()
        time = time + 1
    print("Finished simulation. Time: ", time)
