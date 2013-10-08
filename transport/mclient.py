import math
import pickle
from threading import Lock

from twisted.python import log
from twisted.internet import task
from twisted.internet import reactor
from twisted.internet import protocol
from twisted.protocols.basic import LineReceiver

from cloud.common import *
from cloud.transport.transport import MyTransport

class TransportMasterClientProtocol(LineReceiver):
    def __init__(self, factory):
        self.factory = factory
        self.address = None
        self.waiter = WaitForData(self.factory.fromMasterToMasterClient, self.getData)
        self.waiter.start()
        self.mutexpr = Lock()
        self.mutexsp = Lock()
        self.mytransport = MyTransport(self, "MClient")

    def lineReceived(self, line):
        self.factory.fromMasterClientToMaster.put(line)
        
    def getData(self, packet):
        log.msg("MasterClient: Got a packet from Master, sending it to gsserver")
        log.msg(packet)
        self.sendLine(packet)

    def connectionMade(self):
        task.deferLater(reactor, 2, self.register)
    
    """
    # received data
    def dataReceived(self, fragment):
        self.mytransport.dataReceived(fragment)
    """
    
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
