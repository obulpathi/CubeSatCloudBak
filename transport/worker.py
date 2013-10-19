import os
import math
import pickle
import Image
import ImageFilter

from time import sleep
from twisted.python import log
from twisted.internet import task
from twisted.internet import reactor
from twisted.internet import protocol
from twisted.protocols.basic import LineReceiver

from threading import Lock

from cloud import utils
from cloud.common import *
from cloud.transport.transport import MyTransport

class TransportWorkerProtocol(LineReceiver):
    def __init__(self, factory, homedir):
        self.factory = factory
        self.homedir = os.path.expanduser(homedir)
        self.address = self.factory.address 
        #self.MAX_LENGTH = 64000
        self.cswaiter = WaitForData(self.factory.fromCSServerToWorker, self.getData)
        self.ccwaiter = WaitForData(self.factory.fromCSClientToWorker, self.getReply)
        self.cswaiter.start()
        self.ccwaiter.start()
        self.mutexpr = Lock()
        self.mutexsp = Lock()
        self.fragments = None
        self.fragmentsLength = 0
        self.packetLength = 0
        self.work = None
        self.mytransport = MyTransport(self, "Worker")

    def getData(self, data):
        # strip off the length header
        self.sendLine(data)

    def getReply(self, reply):
        # print "worker got OK, going for next", reply
        if "OK" in reply:
            # print("DOWNLINKED")
            self.getWork(self.work)
        elif "NO" in reply:
            print("ERROR WHILE DOWNLINKING")
        else:
            print "Unokwn message"
            print reply
            
    def connectionMade(self):
        self.register()

    # line received
    def lineReceived(self, line):
        fields = line.split(":")
        destination = fields[0]
        fields = fields[1:]
        if destination != self.address:
            self.factory.fromWorkerToCSServer.put(line)
            return
        command = fields[0]
        if command == "REGISTERED":
            self.registered(fields[1])
        elif command == "NO_WORK":
            self.noWork()
        elif command == "WORK":
            work = Work(fields[1], fields[2], fields[3], None)
            work.size = int(fields[4])
            if work.job == "PROCESS":
                work.payload = fields[5]
            self.gotWork(work)
        else:
            print(line)

    def rawDataReceived(self, data):
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
            self.work.payload = self.fragments
            self.gotWork(self.work)
                            
    # receive packet    
    def packetReceived(self, packet):
        # acquire the mutex
        self.mutexpr.acquire()
        log.msg(packet)
        if self.address == "Worker" and packet.flags == REGISTERED:
            self.registered(packet)
        elif packet.destination == "Server":
            self.forwardToServer(packetstring)
        elif packet.destination != self.address:
            self.forwardToChild(packet)
        elif packet.flags == "NO_WORK":
            self.noWork()
        elif packet.flags == "WORK":
            self.gotWork(packet.payload)
        elif packet.flags == CHUNK:
            self.receivedChunk(packet)
        else:
            log.msg("Server said: %s" % packetstring)
        # release the mutex
        self.mutexpr.release()
    
    # send a packet, if needed using multiple fragments
    def sendPacket(self, packetstring):
        self.mutexsp.acquire()
        length = len(packetstring)
        packetstring = str(length).zfill(LHSIZE) + packetstring
        for i in range(int(math.ceil(float(length)/MAX_PACKET_SIZE))):
            # log.msg("Sending a fragment")
            self.transport.write(packetstring[i*MAX_PACKET_SIZE:(i+1)*MAX_PACKET_SIZE])
        self.mutexsp.release()
    
    def register(self):
        #packet = Packet("Worker", "Server", "Worker", "Server", REGISTER, None, HEADERS_SIZE)
        #packetstring = pickle.dumps(packet)
        # self.sendLine("REGISTER")
        #self.sendPacket(packetstring)
        self.getWork()
        
    def registered(self, address):
        self.address = address
        self.homedir = self.homedir + str(self.address) + "/"
        try:
            os.mkdir(self.homedir)
        except OSError:
            log.msg("OSError: Unable to create home directory, exiting")
            exit()
        self.status = IDLE
        self.getWork(None)
        
    def deregister(self):
        self.transport.loseConnection()

    def getWork(self, work = None):
        if work:
            self.sendLine("WORK:" + self.address + ":" + work.tostr())
        else:
            self.sendLine("WORK:" + self.address + ":")
    
    def noWork(self):
        # log.msg("No work")
        task.deferLater(reactor, 1.0, self.getWork)
    
    def gotWork(self, work):
        # print("Worker got work")
        if work.job == "STORE":
            self.store(work)
            # task.deferLater(reactor, ((C2C_CHUNK_COMMUNICATION_TIME * work.size) / 1000), self.store, work)
        elif work.job == "PROCESS":
            # simulate chunk read
            task.deferLater(reactor, (CHUNK_READ_TIME + CHUNK_WRITE_TIME), self.process, work)
            # self.process(work)
        elif work.job == "DOWNLINK":
            self.downlink(work)
        else:
            log.msg("Unkown work")
            log.msg(work)

    def store(self, work):
        # create the directory, if needed
        directory = self.homedir + os.path.split(work.filename)[0]
        if not os.path.exists(directory):
            os.mkdir(directory)
        work.payload = None
        task.deferLater(reactor, CHUNK_WRITE_TIME, self.getWork, work)
    
    def process(self, work):
        log.msg(work)
        # simulate processing
        task.deferLater(reactor, ((CHUNK_PROCESS_TIME * work.size) / 1000), self.getWork, work)
        
    def downlink(self, work):
        filename = self.homedir + work.filename
        metadata = "CHUNK:" + work.tostr()
        self.forwardToServer(metadata)
        self.work = work
        # wait for downlink ack to call getWork
                   
    def forwardToServer(self, metadata, data = None):
        self.factory.fromWorkerToCSClient.put(metadata)
        # self.factory.fromWorkerToCSClient.put(data)
   
    def forwardToChild(self, packet):
        self.factory.fromWorkerToCSServer.put(packet)

            
class TransportWorkerFactory(protocol.ClientFactory):
    def __init__(self, address, homedir, fromWorkerToCSClient, fromCSClientToWorker, fromWorkerToCSServer, fromCSServerToWorker):
        self.address = str(address)
        self.homedir = homedir
        self.fromWorkerToCSClient = fromWorkerToCSClient
        self.fromCSClientToWorker = fromCSClientToWorker
        self.fromWorkerToCSServer = fromWorkerToCSServer
        self.fromCSServerToWorker = fromCSServerToWorker
        
    def buildProtocol(self, addr):
        return TransportWorkerProtocol(self, self.homedir)
        
    def clientConnectionFailed(self, connector, reason):
        log.msg("Connection failed.")
        reactor.stop()
        
    def clientConnectionLost(self, connector, reason):
        log.msg("Connection lost#######.")
        print connector, reason
        reactor.stop()
