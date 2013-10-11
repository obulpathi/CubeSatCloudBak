#!/usr/bin/env python

import time

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor

class Client(DatagramProtocol):
    stuff = "hi###############################################################################################"
    
    def startProtocol(self):
        self.transport.connect('127.0.0.1', 8000)
        self.sendDatagram()
    
    def sendDatagram(self):
        self.t1 = time.time()
        self.transport.write(self.stuff)

    def datagramReceived(self, datagram, host):
        self.t2 = time.time()
        print 'Datagram received: ', len(datagram)
        print (self.t2 - self.t1)

def main():
    protocol = Client()
    t = reactor.listenUDP(0, protocol)
    reactor.run()

if __name__ == '__main__':
    main()
