import time
import math

from twisted.internet import reactor
from twisted.internet import protocol
from twisted.protocols.basic import LineReceiver

from cloud.common import *

class Client(LineReceiver):
    def __init__(self):
        self.mutex = Lock()
        self.name = "Client"
        self.times = []
        self.sizes = []
        self.setLineMode()
        self.chunkname = ""
        self.fragments = None
        self.fragmentsLength = 0
        self.packetLength = 0
        
    def connectionMade(self):
        print("Client connection made")
        self.requestList()
    
    def connectionLost(self, reason):
        print("connection lost")

    def lineReceived(self, line):
        self.mutex.acquire()
        fields = line.split(":")
        command = fields[0]
        if command == "LIST":
            self.gotList(fields[1:])
        elif command == "CHUNK":
            self.setRawMode()
            self.gotChunkdata(fields[1:])
        else:
            print(line)
        self.mutex.release()

    def rawDataReceived(self, data):
        self.mutex.acquire()
        # buffer the the fragments
        if not self.fragments:
            self.fragments = data
            self.fragmentsLength = len(self.fragments)
        else:
            self.fragments = self.fragments + data
            self.fragmentsLength = self.fragmentsLength + len(data)
        # check if we received all the fragments
        if self.fragmentsLength == self.packetLength:
            self.setLineMode()
            self.gotChunk(self.fragments)
        self.mutex.release()
    
    def requestList(self):
        self.t1 = time.time()
        data = "LIST"
        self.sendLine(data)
    
    def gotList(self, chunks):
        self.t2 = time.time()
        self.chunks = chunks
        print self.chunks
        chunk = self.chunks[0]
        self.requestChunk()
        
    def requestChunk(self):
        self.time = time.time()
        chunk = self.chunks[0]
        self.chunks = self.chunks[1:]
        packet = "CHUNK:" + str(chunk)
        self.sendLine(packet)
    
    def gotChunkdata(self, fields):
        self.chunkname = fields[0]
        self.packetLength = int(fields[1])
        self.fragments = None
        self.fragmentsLength = 0

    def gotChunk(self, data):
        self.times.append(time.time() - self.time)
        print self.times[-1]
        self.sizes.append(self.packetLength)
        length = self.packetLength
        chunkname = self.chunkname
        chunk = open("output/" + chunkname, "w")
        chunk.write(data)
        chunk.close()
        if self.chunks:
            self.requestChunk()
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
    #reactor.connectTCP("localhost", 8000, ClientFactory())
    reactor.connectTCP("10.227.80.45", 8000, ClientFactory())
    #reactor.connectTCP("10.227.80.88", 8000, ClientFactory())
    reactor.run()

# run main
if __name__ == '__main__':
    main()
