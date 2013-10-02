#!/usr/bin/env python

from twisted.internet import reactor
import time

def printTime():
    print "Current time is", time.strftime("%H:%M:%S")

def stopReactor():
    print "Stopping reactor"
    reactor.stop()

reactor.callLater(1, printTime)
reactor.callLater(2, printTime)
reactor.callLater(3, printTime)
reactor.callLater(4, printTime)
reactor.callLater(5, stopReactor)

print "Starting the event loop"
reactor.run()
print "Finished the event loop"
