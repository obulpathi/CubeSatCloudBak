import math
import pickle
from threading import Lock

from twisted.python import log
from twisted.internet import task
from twisted.internet import reactor
from twisted.internet import protocol
from twisted.protocols.basic import LineReceiver

from cloud.common import *
from cloud import utils

class TransportMasterClientProtocol(LineReceiver):
    def __init__(self, factory):
        log.msg("Initializing Transport master Client")
        self.factory = factory
        # self.name = None
        self.waiter = WaitForData(self.factory.fromMasterToMasterClient, self.getData)
        self.waiter.start()
        self.mutexpr = Lock()
        self.mutexsp = Lock()
        # self.MAX_LENGTH = 50000
        self.setLineMode()
        # self.mytransport = MyTransport(self, "MClient")

    def lineReceived(self, line):
        log.msg("Master client got a line, sending to Master")
        log.msg(line)
        self.factory.fromMasterClientToMaster.put(line)
        
    def getData(self, packet):
        log.msg("Master client got a line, sending to SServer")
        log.msg(packet)
        self.sendLine(packet)
        log.msg("Master Client: Sent line to server")

    def connectionMade(self):
        log.msg("transport master client: connection made")
        #self.sendLine("#################################################################")
        self.register()
        # task.deferLater(reactor, 10, self.register)
    
    # received a packet
    def packetReceived(self, packet):
        self.mutexpr.acquire()
        log.msg(packet)
        self.factory.fromMasterClientToMaster.put(packet)
        self.mutexpr.release()

    # send a packet, if needed using multiple fragments
    def sendPacket(self, packetstring):
        self.mutexsp.acquire()
        length = len(packetstring)
        packetstring = str(length).zfill(LHSIZE) + packetstring
        for i in range(int(math.ceil(float(length)/MAX_PACKET_SIZE))):
            self.transport.write(packetstring[i*MAX_PACKET_SIZE:(i+1)*MAX_PACKET_SIZE])
        self.mutexsp.release()
                
    def register(self):
        self.factory.fromMasterClientToMaster.put("REGISTER")
        
    def registered(self, packet):
        log.msg("Whoa!!!!!")
        self.name = packet.payload
        self.status = REGISTERED
        
    def deregister(self):
        self.transport.loseConnection()
        
            
class TransportMasterClientFactory(protocol.ClientFactory):
    # protocol = TransportMasterClientProtocol
    def __init__(self, fromMasterToMasterClient, fromMasterClientToMaster):
        print("Initializing Transport Master Client Factory")
        self.fromMasterToMasterClient = fromMasterToMasterClient
        self.fromMasterClientToMaster = fromMasterClientToMaster
        
    def buildProtocol(self, addr):
        print("Building Transport Master Client Protocol")
        return TransportMasterClientProtocol(self)
    
    def clientConnectionFailed(self, connector, reason):
        log.msg("Connection failed.")
        reactor.stop()
        
    def clientConnectionLost(self, connector, reason):
        log.msg("Connection lost.")
        reactor.stop()
