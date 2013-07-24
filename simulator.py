#!/usr/bin/env python

from cloud.core.master import Master
from cloud.core.slave import Slave
from cloud.core.server import Server
from cloud.core.groundstation import GroundStation
from cloud.core.network import Network

class Simulator(object):
    def __init__(self, config):
        # create master, slaves, server, ground station
        self.master = Master("Master", config.master)
        self.slaves = [Slave("Slave: " + str(i), config.slave) for i in range(config.network_size - 1)]
        self.server = Server("Server")
        self.groundstations = [GroundStation("GroundStation: " + str(i)) for i in range(config.network_size)]   
        # form the network
        self.network = Network(self.master, self.slaves, self.server, self.groundstations)
    
    def start():
        # set upt het network
        network.bootstrap()
        nework.set_up_routes()
    
    def simulate(self):
        # start the modules
        while True:
            self.server.step()
            for groundstation in self.groundstations:
                groundstation.step()
            self.master.step()
            for slave in self.slaves:
                slave.step()
            self.network.step()
            # check for exit conditions

if __name__ == "__main__":
    import yaml
    from cloud.core.common import Struct

    # read the configuration
    f = open('config.yaml')
    configDict = yaml.load(f)
    f.close()
    config = Struct(configDict)
    # create simulator
    mysimulator = Simulator(config)
    mysimulator.simulate()
