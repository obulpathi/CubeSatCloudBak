import os
import time
import utils

# profile for process
def profileProcess(chunks):
    processtimes = []
    for chunk in chunks:
        t1 = time.time()
        data = utils.process("chunks/" + chunk)
        t2 = time.time()
        processtimes.append(t2-t1)
    totalProcesstime = 0
    for processtime in processtimes:
        totalProcesstime = totalProcesstime + processtime
    avgProcesstime = totalProcesstime / len(chunks)
    print "Average process time:", avgProcesstime
    print "Total process time:", totalProcesstime
    print "Number of chunks processed:", len(chunks)
        
# main
if __name__ == "__main__":
    chunks = os.listdir("chunks")
    profileProcess(chunks)
