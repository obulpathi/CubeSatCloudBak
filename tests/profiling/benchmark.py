import os
import time
import utils

# profile for read
def profileRead(images):
    readtimes = []
    for image in images:
        t1 = time.time()
        data = utils.read(image)
        t2 = time.time()
        readtimes.append(t2-t1)
    totalReadtime = 0
    for readtime in readtimes:
        totalReadtime = totalReadtime + readtime
    avgReadtime = totalReadtime / len(images)
    print "Average read time:", avgReadtime
    print "Total read time:", totalReadtime
    print "Number of images read:", len(images)

# profile for write
def profileWrite(images):
    writetimes = []
    for image in images:
        data = utils.read(image) 
        t1 = time.time()
        utils.write("output/" + os.path.split(image)[0], data)
        t2 = time.time()
        writetimes.append(t2-t1)
    totalWritetime = 0
    for writetime in writetimes:
        totalWritetime = totalWritetime + writetime
    avgWritetime = totalWritetime / len(images)
    print "Average write time:", avgWritetime
    print "Total write time:", totalWritetime
    print "Number of images written:", len(images)

# profile for process
def profileProcess(images):
    processtimes = []
    for image in images:
        t1 = time.time()
        data = utils.process(image)
        t2 = time.time()
        processtimes.append(t2-t1)
    totalProcesstime = 0
    for processtime in processtimes:
        totalProcesstime = totalProcesstime + processtime
    avgProcesstime = totalProcesstime / len(images)
    print "Average process time:", avgProcesstime
    print "Total process time:", totalProcesstime
    print "Number of images processed:", len(images)
        
# main
if __name__ == "__main__":
    images = os.listdir("images")
    sets = [["images/10.jpg"], ["images/20.jpg"]]
    #sets = [["images/10.jpg"], ["images/20.jpg"], ["images/50.jpg"], ["images/100.jpg"], ["images/250.jpg"]]
    for files in sets:
        print "Profiling:", files
        profileRead(files)
        profileWrite(files)
        profileProcess(files)
