import os
import time
import utils

# profile for read
def profileRead(chunks):
    readtimes = []
    for chunk in chunks:
        t1 = time.time()
        data = utils.read("chunks/" + chunk)
        t2 = time.time()
        readtimes.append(t2-t1)
    totalReadtime = 0
    for readtime in readtimes:
        totalReadtime = totalReadtime + readtime
    avgReadtime = totalReadtime / len(chunks)
    print avgReadtime, totalReadtime, len(chunks)

# profile for write
def profileWrite(chunks):
    writetimes = []
    for chunk in chunks:
        data = utils.read("chunks/" + chunk) 
        t1 = time.time()
        utils.write("output/" + chunk, data)
        t2 = time.time()
        writetimes.append(t2-t1)
    totalWritetime = 0
    for writetime in writetimes:
        totalWritetime = totalWritetime + writetime
    avgWritetime = totalWritetime / len(chunks)
    print avgWritetime, totalWritetime, len(chunks)

# profile for process
def profileProcess(chunks):
    processtimes = []
    for chunk in chunks:
        t1 = time.time()
        data = utils.process("chunks/" + chunk)
        t2 = time.time()
        processtimes.append(t2-t1)
    totalProcesstimes = 0
    for processtime in processtimes:
        totalProcesstimes = totalProcesstimes + processtime
    avgProcesstimes = totalProcesstimes / len(chunks)
    print avgProcesstimes, totalProcesstimes, len(chunks)
        
# main
if __name__ == "__main__":
    chunks = os.listdir("chunks")
    profileRead(chunks)
    profileWrite(chunks)
    profileProcess(chunks)
