import math
import pickle
from time import sleep
from cloud.common import *
from threading import Lock

# send a packet, if needed using multiple fragments
def sendPacket(module, packetstring):
    module.mutexsp.acquire()
    length = len(packetstring)
    packetstring = str(length).zfill(LHSIZE) + packetstring
    for i in range(int(math.ceil(float(length)/MAX_PACKET_SIZE))):
        module.transport.write(packetstring[i*MAX_PACKET_SIZE:(i+1)*MAX_PACKET_SIZE])
    module.mutexsp.release()

class MyTransport(object):
    def __init__(self, transport, name = "Transport"):
        self.name = name
        self.transport = transport
        self.fragments = ""
        self.fragmentlength = 0
        self.packetlength = 0
        self.mutex = Lock()
    
    def reset(self):
        self.fragments = ""
        self.fragmentlength = 0
        self.packetlength = 0
        
    # received data
    def dataReceived(self, fragment):
        self.mutex.acquire()
        # add the current fragment to fragments
        if self.fragments:
            self.fragments = self.fragments + fragment
            self.fragmentlength = self.fragmentlength + len(fragment)
        else:
            self.packetlength = int(fragment[:LHSIZE])
            self.fragments = fragment[LHSIZE:]
            self.fragmentlength = len(self.fragments)
            print(self.fragmentlength, self.packetlength)
        # if we have more then one packet
        while self.fragmentlength > self.packetlength:
            packetstring = self.fragments[:self.packetlength]
            #print(packetstring)
            packet = pickle.loads(packetstring)
            self.transport.packetReceived(packet)
            # remove old packet from fragments
            self.fragments = self.fragments[self.packetlength:]
            # get the new packets length
            self.packetlength = int(self.fragments[:LHSIZE])
            # remove the packet length header from fragments
            self.fragments = self.fragments[LHSIZE:]
            self.fragmentlength = len(self.fragments)               
        # if we received just one packet
        if self.fragmentlength == self.packetlength:
            packet = pickle.loads(self.fragments)
            self.transport.packetReceived(packet)
            self.fragments = ""
        else: # if we received less than a packet
            print("%s: Received a fragment, waiting for more" % self.name)
        self.mutex.release()
