import os
import math

from twisted.internet import reactor
from twisted.internet import protocol
from twisted.protocols.basic import LineReceiver

from cloud.common import *

class Server(LineReceiver):
    def __init__(self):
        self.mutexpr = Lock()
        self.mutexsp = Lock()
        self.name = "Server"
        self.setLineMode()
        
    def connectionMade(self):
        print("Client connection made")

    def lineReceived(self, line):
        fields = line.split(":")
        command = fields[0]
        if command == "LIST":
            self.sendList()
        elif command == "CHUNK":
            self.sendChunk(fields[1])
        else:
            print line
                        
    def sendData(self, data):
        self.setRawMode()
        length = len(data)
        for i in range(int(math.ceil(float(length)/MAX_PACKET_SIZE))):
            self.transport.write(data[i*MAX_PACKET_SIZE:(i+1)*MAX_PACKET_SIZE])
        self.setLineMode()
            
    def sendList(self):
        chunks = os.listdir("chunks/")
        data = "LIST"
        for chunk in chunks:
            data = data + ":" + chunk
        self.sendLine(data)
            
    def sendChunk(self, chunkname):
        chunk = open("chunks/" + chunkname, "r")
        data = chunk.read()
        chunk.close()
        chunkdata = "CHUNK:" + chunkname + ":" + str(len(data))
        self.sendLine(chunkdata)
        self.sendData(data)
        
def main():
    """Run the server protocol on port 8000"""
    factory = protocol.ServerFactory()
    factory.protocol = Server
    reactor.listenTCP(8000,factory)
    reactor.run()

# run main
if __name__ == '__main__':
    main()
