import time
import math
import pickle

from twisted.internet import reactor
from twisted.internet import protocol

from cloud.common import *
from transport import MyTransport

class Client(protocol.Protocol):
    def __init__(self):
        self.mutexpr = Lock()
        self.mutexsp = Lock()
        self.name = "Client"
        self.times = []
        self.sizes = []
        self.mytransport = MyTransport(self, self.name)
        
    def connectionMade(self):
        print("Client connection made")
        self.requestList()
    
    def connectionLost(self, reason):
        print "connection lost"
        
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
        if packet[:4] == "LIST":
            chunks = pickle.loads(packet[4:])
            self.gotList(chunks)
        elif packet[:5] == "CHUNK":
            self.gotChunk(packet[5:])
        else:
            print("DHSGDJHGSDJSD^&%$#^&@#&^@%#&^#&#@&$&")
    
    def requestList(self):
        self.t1 = time.time()
        packet = "LIST"
        self.sendPacket(packet)
    
    def gotList(self, chunks):
        self.t2 = time.time()
        self.chunks = chunks
        chunk = self.chunks[0]
        self.chunks = self.chunks[1:]
        self.requestChunk(chunk)
        
    def requestChunk(self, chunk):
        self.time = time.time()
        packet = "CHUNK" + str(chunk)
        self.sendPacket(packet)
    
    def gotChunk(self, data):
        self.times.append(time.time() - self.time)
        self.sizes.append(len(data))
        length = int(data[:2])
        chunkname = data[2:length+2]
        data = data[2+length:]
        data = pickle.loads(data)
        chunk = open("output/" + chunkname, "w")
        chunk.write(data)
        chunk.close()
        if self.chunks:
            chunk = self.chunks[0]
            self.chunks = self.chunks[1:]
            self.requestChunk(chunk)
        else:
            print("Finished downlinking chunks")
            self.printStats()
    
    def printStats(self):
        totalSize = 0
        for size in self.sizes:
            totalSize = totalSize + size
        avgSize = totalSize / len(self.sizes)
        totalTime = 0
        for dtime in self.times:
            totalTime = totalTime + dtime
        avgTime = totalTime / len(self.times)
        print "RTT: ", (self.t2 - self.t1)
        print "Average time: ", avgTime
        print "Average size: ", avgSize
        print"Total time: ", totalTime, "Chunks# ", len(self.times)
        
class ClientFactory(protocol.ClientFactory):
    protocol = Client

    def clientConnectionFailed(self, connector, reason):
        print "Connection failed - goodbye!"
        reactor.stop()
    
    def clientConnectionLost(self, connector, reason):
        print "Connection lost - goodbye!"
        reactor.stop()


# this connects the protocol to a server runing on port 8000
def main():
    f = ClientFactory()
    reactor.connectTCP("localhost", 8000, f)
    # reactor.connectTCP("10.227.80.45", 8000, f)
    reactor.run()

# run main
if __name__ == '__main__':
    main()
