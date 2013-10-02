from twisted.internet import reactor, defer
from connectiontester import testConnect

def handleAllResults(allResults, ports):
    for port, results in zip(ports, allResults):
        success, result = results
        if success:
            print "Connected to port %i" % port
    reactor.stop()

import sys
host = sys.argv[1]
ports = range(1, 201)
testers = [testConnect(host, port) for port in ports]
defer.DeferredList(testers, consumeErrors=True).addCallback(
    handleAllResults, ports)
reactor.run()
