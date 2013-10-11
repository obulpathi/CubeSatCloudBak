#!/usr/bin/env python

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor

# Here's a UDP version of the simplest possible protocol
class Server(DatagramProtocol):
    def datagramReceived(self, datagram, address):
        datagram = open("chunk.jpg", "r").read()
        self.transport.write(datagram, address)

def main():
    reactor.listenUDP(8000, Server())
    reactor.run()

if __name__ == '__main__':
    main()
