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
    
    def start(self):
        # set upt het network
        # self.network.bootstrap()
        # self.network.set_up_routes()
        # start individual components
        filename = self.master.sense()
        self.master.createChunks(filename)
        self.master.start()
        for slave in self.slaves:
            slave.start()
        self.server.start()
        for groundstation in self.groundstations:
            groundstation.start()
        self.network.start()
    
    def stop(self):
        # wait for all threads to finish
        self.master.join()
        for slave in self.slaves:
            slave.join()
        self.server.join()
        for groundstation in self.groundstations:
            groundstation.join()
        self.network.join()
        
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
    mysimulator.start()
    # create mission for cubesat cluster
    mission = Mission('CDFS')
    server.addJob(mission)
    mysimulator.stop()
