import math
import pickle
import threading

from twisted.python import log
from twisted.internet import task
from twisted.internet import reactor
from twisted.internet import protocol
from twisted.protocols.basic import LineReceiver

from cloud.common import *
from cloud.transport.transport import MyTransport
            
class TransportGSClientProtocol(LineReceiver):
    def __init__(self, factory):
        self.factory = factory
        self.address = "GroundStation"
        self.metadata = None
        self.mode = "LINE"
        self.waiter = WaitForData(self.factory.fromGSServerToGSClient, self.getData)
        self.waiter.start()
        self.state = UNREGISTERED # whats the begin state?
        self.mytransport = MyTransport(self, "GSClient")
        
    def getData(self, data):
        if self.mode == "LINE":
            self.metadata = data
            self.sendLine(data)
            self.mode = "RAW"
        else:
            self.transport.write(data)
            self.mode = "LINE"
        
    def connectionMade(self):
        log.msg("Connection made")
        # self.register()

    def lineReceived(self, line):
        self.uplinkToCubeSat(line)
        print("###################### GSClient: ", line)
        
    """
    # received data
    def dataReceived(self, fragment):
        self.mytransport.dataReceived(fragment)
    """
                
    # received a packet
    def packetReceived(self, packet):
        log.msg(packet)
        if self.address == "GroundStation" and packet.flags == REGISTERED:
            self.registered(packet)
        elif packet.destination != self.address:
            self.uplinkToCubeSat(pickle.dumps(packet))
        else:
            log.msg("Server said: %s " % packet)

    # send a packet, if needed using multiple fragments
    def sendPacket(self, packetstring):
        length = len(packetstring)
        packetstring = str(length).zfill(LHSIZE) + packetstring
        for i in range(int(math.ceil(float(length)/MAX_PACKET_SIZE))):
            self.transport.write(packetstring[i*MAX_PACKET_SIZE:(i+1)*MAX_PACKET_SIZE])
                
    def register(self):
        packet = Packet(self.address, "Server", self.address, "Server", REGISTER, None, HEADERS_SIZE)
        packetstring = pickle.dumps(packet)
        self.sendPacket(packetstring)
        log.msg(packet)
        
    def registered(self, packet):
        self.address = packet.payload
        self.status = REGISTERED
        
    def deregister(self):
        log.msg("TODO: Deregistration")
        self.transport.loseConnection()
    
    def uplinkToCubeSat(self, packetstring):
        #log.msg("Groung station: Uplinking to CubeSat >>>>>>>>>>>>>>>>>>")
        #length = len(packetstring)
        #packetstring = str(length).zfill(LHSIZE) + packetstring
        self.factory.fromGSClientToGSServer.put(packetstring)


class TransportGSClientFactory(protocol.ClientFactory):
    def __init__(self, fromGSClientToGSServer, fromGSServerToGSClient):
        self.fromGSClientToGSServer = fromGSClientToGSServer
        self.fromGSServerToGSClient = fromGSServerToGSClient
        
    def buildProtocol(self, addr):
        return TransportGSClientProtocol(self)
        
    def clientConnectionFailed(self, connector, reason):
        log.msg("Connection failed.")
        reactor.stop()
        
    def clientConnectionLost(self, connector, reason):
        log.msg("Connection lost.")
        reactor.stop()
