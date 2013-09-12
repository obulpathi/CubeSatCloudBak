import math
import pickle

from twisted.python import log
from twisted.internet import task
from twisted.internet import reactor
from twisted.internet import protocol

from cloud.common import *

class TransportMasterClientProtocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory
        self.address = None
        self.waiter = WaitForData(self.factory.fromMasterToMasterClient, self.getData)
        self.waiter.start()
        self.fragments = ""
        self.fragmentlength = 0
        self.packetlength = 0

    def getData(self, packet):
        log.msg("MasterClient: Got a packet from Master, sending it to gsserver")
        log.msg(packet)
        self.sendPacket(pickle.dumps(packet))

    def connectionMade(self):
        task.deferLater(reactor, 2, self.register)

    # received data
    def dataReceived(self, fragment):
        # add the current fragment to fragments
        if self.fragments:
            log.msg("Received another fragment")
            self.fragments = self.fragments + fragment
            self.fragmentlength = self.fragmentlength + len(fragment)
        else:
            log.msg("Received a new fragment")
            self.packetlength = int(fragment[:6])
            self.fragmentlength = len(fragment)
            self.fragments = fragment[6:]

        # check if we received the whole packet
        if self.fragmentlength == self.packetlength:
            packet = pickle.loads(self.fragments)
            self.fragments = ""
            self.packetReceived(packet)
        elif self.fragmentlength >= self.packetlength:
            print(self.fragmentlength, self.packetlength)
            print(self.fragments)
            log.msg("Unhandled exception: self.fragmentlength >= self.packetlength")
            exit(1)
        else:
            pass

    # received a packet
    def packetReceived(self, packet):
        log.msg(packet)
        self.factory.fromMasterClientToMaster.put(packet)

    # send a packet, if needed using multiple fragments
    def sendPacket(self, packetstring):
        length = len(packetstring) + 6
        packetstring = str(length).zfill(6) + packetstring
        print(length, packetstring[:6])
        for i in range(int(math.ceil(float(length)/MAX_PACKET_SIZE))):
            log.msg("fgragment: %d\t len: %d" % (i, len(packetstring[i*MAX_PACKET_SIZE:(i+1)*MAX_PACKET_SIZE])))
            log.msg("Sending a fragment")
            self.transport.write(packetstring[i*MAX_PACKET_SIZE:(i+1)*MAX_PACKET_SIZE])
            #self.transport.doWrite()
                
    def register(self):
        packet = Packet("MasterClient", "Master", "MasterClient", "Master", REGISTER, None, HEADERS_SIZE)
        self.factory.fromMasterClientToMaster.put(packet)
        
    def registered(self, packet):
        log.msg("Whoa!!!!!")
        self.address = packet.payload
        self.status = REGISTERED
        
    def deregister(self):
        self.transport.loseConnection()
        
            
class TransportMasterClientFactory(protocol.ClientFactory):
    def __init__(self, fromMasterToMasterClient, fromMasterClientToMaster):
        self.fromMasterToMasterClient = fromMasterToMasterClient
        self.fromMasterClientToMaster = fromMasterClientToMaster
        
    def buildProtocol(self, addr):
        return TransportMasterClientProtocol(self)
        
    def clientConnectionFailed(self, connector, reason):
        log.msg("Connection failed.")
        reactor.stop()
        
    def clientConnectionLost(self, connector, reason):
        log.msg("Connection lost.")
        reactor.stop()
