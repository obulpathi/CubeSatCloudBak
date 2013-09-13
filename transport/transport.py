# replace 6 with header length
# undo any hardcoded stuff ... OK :)

import pickle
from cloud.common import *

class MyTransport(object):
    def __init__(self, name = "Transport"):
        self.name = name
        self.fragments = ""
        self.fragmentlength = 0
        self.packetlength = 0
    
    def reset(self):
        self.fragments = ""
        self.fragmentlength = 0
        self.packetlength = 0
        
    # received data
    def dataReceived(self, fragment):
        print("%s: Received a fragment" % self.name)
        # add the current fragment to fragments
        if self.fragments:
            print("%s: Received another fragment" % self.name)
            self.fragments = self.fragments + fragment
            self.fragmentlength = self.fragmentlength + len(fragment)
        else:
            print("%s: Received a new fragment" % self.name)
            self.packetlength = int(fragment[:6])
            self.fragmentlength = len(fragment)
            self.fragments = fragment[6:]

        # check if we received the whole packet
        if self.fragmentlength == self.packetlength:
            packet = pickle.loads(self.fragments)
            self.fragments = ""
            return packet
        elif self.fragmentlength >= self.packetlength:
            print(self.fragmentlength, self.packetlength)
            print("%s: self.fragmentlength >= self.packetlength" % self.name)
            packetstring = self.fragments[:self.packetlength-6]
            self.fragmentlength = self.fragmentlength - self.packetlength
            self.packetlength = self.fragments[self.packetlength-6:self.packetlength]
            self.fragments = self.fragments[int(self.packetlength):]
            packet = pickle.loads(packetstring)
            return packet
        else:
            print("%s: Received a fragment, waiting for more" % self.name)
            return None
