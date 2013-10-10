import os
import time
import utils

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
    print "Average write time:", avgWritetime
    print "Total write time:", totalWritetime
    print "Number of chunks written:", len(chunks)

# main
if __name__ == "__main__":
    chunks = os.listdir("chunks")
    profileWrite(chunks)
