import os
import math
import pickle

from twisted.internet import reactor
from twisted.internet import protocol

from cloud.common import *
from transport import MyTransport

class Server(protocol.Protocol):
    def __init__(self):
        self.mutexpr = Lock()
        self.mutexsp = Lock()
        self.name = "Server"
        self.mytransport = MyTransport(self, self.name)
        
    def connectionMade(self):
        print("Worker connection made")
    
    def dataReceived(self, fragment):
        self.mytransport.dataReceived(fragment)
        
    # send a packet, if needed using multiple fragments
    def sendPacket(self, packetstring):
        self.mutexsp.acquire()
        length = len(packetstring)
        packetstring = str(length).zfill(LHSIZE) + packetstring
        for i in range(int(math.ceil(float(length)/MAX_PACKET_SIZE))):
            self.transport.write(packetstring[i*MAX_PACKET_SIZE:(i+1)*MAX_PACKET_SIZE])
        self.mutexsp.release()
        
    # received a packet
    def packetReceived(self, packet):
        if packet == "LIST":
            self.sendList()
        elif packet[:5] == "CHUNK":
            self.sendChunk(packet[5:])
        else:
            print(packet)
            
    def sendList(self):
        chunks = os.listdir("chunks")
        packet = "LIST" + pickle.dumps(chunks)
        self.sendPacket(packet)
            
    def sendChunk(self, chunkname):
        chunk = open("chunks/" + chunkname, "r")
        data = chunk.read()
        chunk.close()
        picklestring = "CHUNK" + str(len(chunkname)).zfill(2) + chunkname + pickle.dumps(data)
        length = len(picklestring)
        data = str(length).zfill(6) + picklestring
        self.transport.write(data)
        
def main():
    """Run the server protocol on port 8000"""
    factory = protocol.ServerFactory()
    factory.protocol = Server
    reactor.listenTCP(8000,factory)
    reactor.run()

# run main
if __name__ == '__main__':
    main()
