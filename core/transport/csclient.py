import pickle

from twisted.internet import task
from twisted.internet import reactor
from twisted.internet import protocol

from cloud.core.common import *

class TransportCSClientProtocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory
        #loopcall = task.LoopingCall(self.pollForDataFromWorker)
        #loopcall.start(0.1) # call every second

    def pollForDataFromWorker(self):
        print("in loopcall")
        try:
            data = self.factory.fromMasterToCSClient.get(False)
            print("polling for data")
            if data:
                self.transport.write(data)
        except Exception:
            pass
            #print("Exception")

    def connectionMade(self):
        print("CSClient -> GSServer Connection made")
        self.register()
    
    def dataReceived(self, packetstring):
        packet = pickle.loads(packetstring)
        print("data received")
        if packet.flags == REGISTERED:
            self.registered(packet)
        else:
            print("sending data to worker")
            print(packet)
            self.factory.fromCSClientToWorker.put(packet)
    
    def register(self):
        print("registering with ground station and server")
        packet = Packet(self.factory.address, "ground station", self.factory.address, SERVER_ID, REGISTER, None, HEADERS_SIZE)
        data = pickle.dumps(packet)
        self.transport.write(data)
        
    def registered(self, packet):
        print("Whoa!!!!! >>> CubeSatClient Registered with Server #################")
        self.status = REGISTERED
        self.getCommand()
        
    def deregister(self):
        print("TODO: DEREGISTRAITON >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        self.transport.loseConnection()
    
    def getCommand(self):
        print("requesting server for command")
        packet = Packet(self.factory.address, "ground station", self.factory.address, SERVER_ID, COMMAND, None, HEADERS_SIZE)
        data = pickle.dumps(packet)
        self.transport.write(data)
            
    def downlinkToGroundStation(self, packet):
        self.transport.write(packetstring)
    
    def uplinkFromGroundStation(self, packet):
        pass


class TransportCSClientFactory(protocol.ClientFactory):
    def __init__(self, address, fromWorkerToCSClient, fromCSClientToWorker):
        self.address = address
        self.fromWorkerToCSClient = fromWorkerToCSClient
        self.fromCSClientToWorker = fromCSClientToWorker
    def buildProtocol(self, addr):
        return TransportCSClientProtocol(self)
    def clientConnectionFailed(self, connector, reason):
        print "Connection failed."
        reactor.stop()
    def clientConnectionLost(self, connector, reason):
        print "Connection lost."
        reactor.stop()
