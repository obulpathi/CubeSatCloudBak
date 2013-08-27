import sys
from multiprocessing import Queue

from twisted.python import log
from twisted.internet import reactor
from twisted.internet import protocol

from cloud.common import *
from cloud.transport.master import *
from cloud.transport.csclient import *

# simulate sensing and return filename containing the remote sensing data
def sense(self):
    return "image.jpg"

# split the remote sensing data into chunks
def createChunks(self, filename):
    sensor_data = Image.open(filename)
    width = sensor_data.size[0]
    height = sensor_data.size[1]
    for y in range(0, int(math.ceil(float(height)/chunk_y))):
        for x in range(0, int(math.ceil(float(width)/chunk_x))):
            left = x * chunk_x
            top = y * chunk_y
            right = min((x+1) * chunk_x, width)
            bottom = min((y+1) * chunk_y, height)
            box = (left, top, right, bottom)
            chunk = sensor_data.crop(box)
            filename = "chunks/chunk:" + str(y) + "x" + str(x) + ".jpg"
            chunk.save(filename)
            chunkid = str(uuid.uuid4())
            size = os.stat(filename).st_size
            self.chunks.append(Chunk(chunkid, filename, size, box))
            print self.chunks[-1]

# run master
if __name__ == "__main__":
    # set up logging
    #log.startLogging(open('/var/log/master.log', 'w'))
    log.startLogging(sys.stdout)
    #set up IPC channels    
    fromWorkerToCSClient = Queue()
    fromCSClientToWorker = Queue()

    reactor.listenTCP(8000, TransportMasterFactory(fromWorkerToCSClient, fromCSClientToWorker))
    reactor.connectTCP("localhost", 4004, TransportCSClientFactory(MASTER_ID, fromWorkerToCSClient, fromCSClientToWorker))
    

    log.msg("Master is up and running")
    reactor.run()
