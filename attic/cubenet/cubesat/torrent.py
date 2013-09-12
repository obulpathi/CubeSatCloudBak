#!/usr/bin/env python

from cubenet.torrent.slave import Slave
from cubenet.torrent.master import Master
from cubenet.core.server import Server
from cubenet.core.groundstation import GroundStation
from cubenet.core.network import Network
from cubenet.core.common import *
#from common import master_configuration, slave_configuration 
import logging

# time
time = 0
num_of_nodes = 20

# setup logging
logging.basicConfig(filename = 'simulation.log', level = logging.DEBUG)
logger = logging.getLogger("Torrent")

# create master
logger.debug("Creating Master")
master = Master("Master", master_configuration)
logger.debug("Finished creating Master")

# create slaves
logger.debug("Creating slaves")
slaves = []
for i in range(num_of_nodes - 1):
    slaves.append(Slave("Slave " + str(i), slave_configuration))
logger.debug("Finished creating slaves")

# create Server
logger.debug("Creating Server")
server = Server("Server")
logger.debug("Finished creating Server")

# create groundstations
logger.debug("Creating Ground Stations")
groundstations = []
for i in range(num_of_nodes):
    groundstations.append(GroundStation(i))
logger.debug("Finished creating Ground Stations")

# create network
logger.debug("Creating Network")
network = Network(master, slaves, server, groundstations)
logger.debug("Finished creating Network")

# bootstrap network
logger.debug("Bootstrapping Network")
network.bootstrap()
network.buildGraph()
logger.debug("Finished bootstrapping Network")

# print network
# network.show()

# start the network
logger.debug("Starting the network")
network.start()
logger.debug("Started the network")

logger.debug("Starting simulation")

# Create job and assign job to server
logger.debug("Creating job for master")
# size = 100 * MB
payload = "lat lon resolution blah blah blah ... "
size = 4 * MB
job = Torrent(payload, size, [])
server.addJob(job)
logger.debug("Finished creating job for master")

# wait for network to finish jobs
while master.status != FINISHED:
    logger.debug("Time: " + str(time))
    server.step()
    for groundstation in groundstations:
        groundstation.step()
    master.step()
    for slave in slaves:
        slave.step()
    time = time + 1
    
logger.debug("Finished simulation")
network.show()
logging.shutdown()
