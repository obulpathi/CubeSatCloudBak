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
        self.address = "Worker"
        self.cswaiter = WaitForData(self.factory.fromCSServerToWorker, self.getData)
        self.ccwaiter = WaitForData(self.factory.fromCSClientToWorker, self.getData)
        self.cswaiter.start()
        self.ccwaiter.start()
        self.mutexpr = Lock()
        self.mutexsp = Lock()
        self.mytransport = MyTransport(self, "Worker")

    def getData(self, data):
        # strip off the length header
        self.sendPacket(data)

    def connectionMade(self):
        log.msg("Worker connection made >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.")
        self.register()

    """
    # received data
    def dataReceived(self, fragment):
        self.mytransport.dataReceived(fragment)
    """
    # line received
    def lineReceived(self, line):
        fields = line.split(":")
        command = fields[0]
        if command == "REGISTERED":
            self.registered(fields[1])
        elif command == "NO_WORK":
            self.noWork()
        elif command == "WORK":
            work = Work(fields[1], fields[2], fields[3], None)
            if work.job == "PROCESS":
                work.payload = fields[4]
            self.gotWork(work)
            if work.job == "STORE":
                self.setRawMode()
        else:
            print(line)

    def rawDataReceived(self, data):
        # utils.banner("RAW_DATA")
        self.setLineMode()
        self.work.payload = data
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
            log.msg("Sending a fragment")
            self.transport.write(packetstring[i*MAX_PACKET_SIZE:(i+1)*MAX_PACKET_SIZE])
        self.mutexsp.release()
    
    def register(self):
        #packet = Packet("Worker", "Server", "Worker", "Server", REGISTER, None, HEADERS_SIZE)
        #packetstring = pickle.dumps(packet)
        self.sendLine("REGISTER")
        #self.sendPacket(packetstring)
        
    def registered(self, address):
        # utils.banner("REGISTERED")
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
        #packet = Packet(self.address, "Receiver", self.address, "Server", "GET_WORK", work, HEADERS_SIZE)
        #packetstring = pickle.dumps(packet)
        #self.sendPacket(packetstring)
    
    def noWork(self):
        log.msg("No work")
        task.deferLater(reactor, 1.0, self.getWork)
    
    def gotWork(self, work):
        if work.job == "STORE":
            if work.payload:
                self.store(work)
            else:
                self.work = work
        elif work.job == "PROCESS":
            self.process(work)
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
        chunk = open(self.homedir + work.filename, "w")
        chunk.write(work.payload)
        chunk.close()
        self.getWork(Work(work.uuid, work.job, work.filename, None))
    
    def process(self, work):
        log.msg(work)
        # create the directory, if needed
        directory = self.homedir + work.payload + "/"
        if not os.path.exists(directory):
            os.mkdir(directory)
        filename = self.homedir + work.filename
        image = Image.open(filename)
        edges = image.filter(ImageFilter.FIND_EDGES)
        edges.save(directory + os.path.split(work.filename)[1])
        task.deferLater(reactor, 1.0, self.getWork, work)
        
    def downlink(self, work):
        filename = self.homedir + work.filename
        log.msg(filename)
        data = open(filename).read()
        log.msg(work)
        work.payload = str(len(data))
        metadata = "CHUNK:" + work.tostr()
        self.forwardToServer(metadata, data)
        task.deferLater(reactor, 5.0, self.getWork, Work(work.uuid, work.job, work.filename, None))
        """
        work.payload = data
        packet = Packet(self.address, "Receiver", self.address, "Server", "CHUNK", work, HEADERS_SIZE)
        packetstring = pickle.dumps(packet)
        self.forwardToServer(packetstring)
        """
                   
    def forwardToServer(self, metadata, data):
        self.factory.fromWorkerToCSClient.put(metadata)
        self.factory.fromWorkerToCSClient.put(data)
        """
        length = len(data)
        for i in range(int(math.ceil(float(length)/MAX_PACKET_SIZE))):
            log.msg("Sending a fragment")
            self.factory.fromWorkerToCSClient.put(data[i*MAX_PACKET_SIZE:(i+1)*MAX_PACKET_SIZE])
        """    
    def forwardToChild(self, packet):
        self.factory.fromWorkerToCSServer.put(packet)

            
class TransportWorkerFactory(protocol.ClientFactory):
    def __init__(self, address, homedir, fromWorkerToCSClient, fromCSClientToWorker, fromWorkerToCSServer, fromCSServerToWorker):
        self.address = address
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
        log.msg("Connection lost.")
        reactor.stop()
