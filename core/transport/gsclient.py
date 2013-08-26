import pickle

from twisted.internet import task
from twisted.internet import reactor
from twisted.internet import protocol

from cloud.core.common import *

class TransportGSClientProtocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory
        self.id = None
        loopcall = task.LoopingCall(self.pollForDataFromGSServer)
        loopcall.start(0.1) # call every second

    def pollForDataFromGSServer(self):
        try:
            data = self.factory.fromGSServerToGSClient.get(False)
            if data:
                self.transport.write(data)
        except Exception:
            pass

    def connectionMade(self):
        print("GSClient connection made")
        self.register()
    
    def dataReceived(self, packetstring):
        packet = pickle.loads(packetstring)
        print("data received")
        print(packet)
        if self.id and packet.destination != self.id:
            print("Destination: ", packet.destination)
            print("uplinking data to cubesat")
            self.uplinkToCubeSat(packet)
        elif packet.flags & REGISTERED:
            self.registered(packet)
        elif packet.flags & CHUNK:
            self.receivedChunk(packet)
        else:
            print "Server said:", packetstring
    
    def register(self):
        print("registering")
        packet = Packet("GroundStation", MASTER_ID, "GroundStation", MASTER_ID, REGISTER, None, HEADERS_SIZE)
        data = pickle.dumps(packet)
        self.transport.write(data)
        
    def registered(self, packet):
        print("Whoa!!!!!")
        self.id = packet.payload
        self.status = REGISTERED
        
    def deregister(self):
        print("TODO: DEREGISTRAITON >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        self.transport.loseConnection()
    
    def downlinkFromCubeSat(self, packet):
        self.transport.write(packetstring)
    
    def uplinkToCubeSat(self, packet):
        print("sending data througn pipes")
        self.factory.fromGSClientToGSServer.put(packet)


class TransportGSClientFactory(protocol.ClientFactory):
    def __init__(self, fromGSClientToGSServer, fromGSServerToGSClient):
        self.fromGSClientToGSServer = fromGSClientToGSServer
        self.fromGSServerToGSClient = fromGSServerToGSClient
    def buildProtocol(self, addr):
        return TransportGSClientProtocol(self)
    def clientConnectionFailed(self, connector, reason):
        print "Connection failed."
        reactor.stop()
    def clientConnectionLost(self, connector, reason):
        print "Connection lost."
        reactor.stop()
