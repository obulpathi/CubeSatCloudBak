# replace 6 with header length
# undo any hardcoded stuff ... OK :)

import pickle
from cloud.common import *
from threading import Lock

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
        # print("%s: Received a fragment" % self.name)
        # add the current fragment to fragments
        if self.fragments:
            print("%s: Received another fragment" % self.name)
            self.fragments = self.fragments + fragment
            self.fragmentlength = self.fragmentlength + len(fragment)
        else:
            print("%s: Received a new fragment" % self.name)
            self.packetlength = int(fragment[:LHSIZE])
            self.fragmentlength = len(fragment)
            self.fragments = fragment[LHSIZE:]

        # if we have more then one packet
        while self.fragmentlength > self.packetlength:
            print("%s: fragmentlength: %d,\tpacketlength: %d" % (self.name, self.fragmentlength, self.packetlength))
            packetstring = self.fragments[:self.packetlength-LHSIZE]
            packet = pickle.loads(packetstring)
            self.transport.packetReceived(packet)
            self.fragmentlength = self.fragmentlength - self.packetlength
            self.packetlength = int(self.fragments[self.packetlength-LHSIZE:self.packetlength])
            self.fragments = self.fragments[self.packetlength:]
            print("%s: fragmentlength: %d,\tpacketlength: %d" % (self.name, self.fragmentlength, self.packetlength))               
        # if we received just one packet
        if self.fragmentlength == self.packetlength:
            packetstring = self.fragments[:self.packetlength-LHSIZE]
            packet = pickle.loads(packetstring)
            # packet = pickle.loads(self.fragments)
            self.transport.packetReceived(packet)
            self.reset()
        else: # if we received less than a packet
            print("%s: Received a fragment, waiting for more" % self.name)
            
        self.mutex.release()
