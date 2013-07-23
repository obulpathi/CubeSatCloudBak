#!/usr/bin/env python

from cloud.core.master import Master
from cloud.core.slave import Slave

class Simulator(object):
	def __init__(self, config):
		# create master, slaves, server, ground station
		master = Master("Master", config.master)
		slaves = [Slaves()]
		server = Server()
		groundstations = [GrounsStation()]
	
		# form the network
		network = Network(master, slaves, server, groundstations)
	
	def start():
		# set upt het network
		network.bootstrap()
		nework.set_up_routes()
	
	def simulate(self):
		# start the modules
		while True:
			server.step()
			for groundstation in groundstations():
				groundstation.step()
			master.step()
			for slave in slaves:
				slave.step()
			network.step()
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
