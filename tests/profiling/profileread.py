import os
import time
import utils

# profile for read
def profileRead(chunks):
    chunksizes = []
    readtimes = []
    for chunk in chunks:
        t1 = time.time()
        data = utils.read("chunks/" + chunk)
        t2 = time.time()
        readtimes.append(t2-t1)
        chunksizes.append(len(data))
    totalReadtime = 0
    for readtime in readtimes:
        totalReadtime = totalReadtime + readtime
    avgReadtime = totalReadtime / len(chunks)
    totalChunksize = 0
    for chunksize in chunksizes:
        totalChunksize = totalChunksize + chunksize
    avgChunksize = totalChunksize / len(chunksizes)
    print "Average read time:", avgReadtime
    print "Total read time:", totalReadtime
    print "Average chunk size:", avgChunksize
    print "Total chunk size:", totalChunksize
    print "Number of chunks read:", len(chunks)
        
# main
if __name__ == "__main__":
    chunks = os.listdir("chunks")
    profileRead(chunks)
