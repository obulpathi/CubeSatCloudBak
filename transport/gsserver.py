import pickle
from threading import Lock

from twisted.python import log
from twisted.internet import reactor
from twisted.internet import protocol
from twisted.protocols.basic import LineReceiver

from cloud import utils
from cloud.common import *

class TransportGSServerProtocol(LineReceiver):
    def __init__(self, factory):
        self.factory = factory
        self.mode = "LINE"
        self.work = None
        self.fragments = None
        self.fragmentsLength = 0
        self.packetLength = 0
        self.waiter = WaitForData(self.factory.fromGSClientToGSServer, self.getData)
        self.waiter.start()
        self.mutex = Lock()
        self.setLineMode()

    def getData(self, line):
        log.msg("GSServer: Got a packet, uplinking to worker")
        self.sendLine(line)
    
    def lineReceived(self, line):
        self.mutex.acquire()
        self.setRawMode()
        # print("GS Server line received")
        fields = line.split(":")
        self.work = Work(fields[1], fields[2], fields[3], None)
        self.work.size = fields[4]
        self.packetLength = int(self.work.size)
        self.fragments = None
        self.fragmentsLength = 0
        self.factory.fromGSServerToGSClient.put(line)
        self.mode = "RAW"
        self.mutex.release() 

    def rawDataReceived(self, data):
        self.mutex.acquire()
        # log.msg("GS Server: received data")
        self.factory.fromGSServerToGSClient.put(data)
        # buffer the the fragments
        if not self.fragments:
            # log.msg("first fragment")
            self.fragments = data
            self.fragmentsLength = len(self.fragments)
            print self.fragmentsLength, self.packetLength
        else:
            # log.msg("more fragment")
            self.fragments = self.fragments + data
            self.fragmentsLength = self.fragmentsLength + len(data)
        # check if we received all the fragments
        if self.fragmentsLength == self.packetLength:
            self.mode = "LINE"
            self.setLineMode()
            self.sendLine("OK:Ground Station server received data and acked Ground Station server received data and acked")
            # log.msg("GS Server: received data and acked")
        elif self.fragmentsLength > self.packetLength:
            utils.banner("ERROR: self.fragmentsLength > self.packetLength")
        else:
            log.msg("GS server: waiting for more fragmetns")
        self.mutex.release()
        
class TransportGSServerFactory(protocol.Factory):
    def __init__(self, fromGSClientToGSServer, fromGSServerToGSClient):
        self.fromGSClientToGSServer = fromGSClientToGSServer
        self.fromGSServerToGSClient = fromGSServerToGSClient
        
    def buildProtocol(self, addr):
        return TransportGSServerProtocol(self)
