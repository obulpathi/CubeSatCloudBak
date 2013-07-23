#!/usr/bin/env python

import networkx as nx
from cloud.core.common import *
from cloud.core.topology import *
from cloud.core.transceiver import Transceiver
from matplotlib import pyplot

class Network(object):
    def __init__(self, master, slaves, server, groundstations):
        self.graph = nx.Graph()
        self.master = master
        self.slaves = slaves
        self.nodes = [self.master] + self.slaves
        self.server = server
        self.relay = groundstations[0]
        self.groundstations = groundstations
    
    def init(self):
        self.master.init(self.graph, self.nodes)
        for slave in self.slaves:
            slave.init(self.graph, self.nodes)
        self.server.init()
        for groundstation in self.groundstations:
            groundstation.init()
        
    # establish the links and bootstrap the network
    def bootstrap(self):
        self.master.setSlaves(self.slaves)
        for slave in self.slaves:
            slave.setMaster(self.master)
        self.server.setMaster(self.master)
        self.master.setServer(self.server)
        self.master.connect(self.relay) # master.setRelay
        self.relay.connect(self.master) # relay.setMaster
        self.server.setRelayGroundstation(self.groundstations[0])
        for cubesat, groundstation in zip(self.slaves, self.groundstations[1:]):
            cubesat.connect(groundstation)
            groundstation.connect(cubesat)
        # set the network
        self.master.setNetwork(self)
        self.server.setNetwork(self)
        for slave in self.slaves:
            slave.setNetwork(self)
        for groundstation in self.groundstations:
            groundstation.setNetwork(self)
        
    # build the network
    def buildGraph(self):
        nodes = [self.master] + self.slaves
        self.graph = atom(nodes)
        
    def buildLinks(self):
        # create and configure the traceivers and links
        for (nodeX, nodeY) in self.graph.edges():
            transceiverX = Transceiver(nodeX.received, None, str(nodeY.name) + " -> " + str(nodeX.name), CS2CSLink)
            transceiverY = Transceiver(nodeY.received, None, str(nodeX.name) + " -> " + str(nodeY.name), CS2CSLink)
            transceiverX.setOther(transceiverY)
            transceiverY.setOther(transceiverX)
            nodeX.transceivers[nodeY] = transceiverX
            nodeY.transceivers[nodeX] = transceiverY
        
    # set up the links
    def links(self):
        global nodes
        global graph
        for edge in graph.edges():
            distance = edge.distance # store distance, bandwidth, latency as properties for links
            # based on distance, assign power, bandwidth, latency using lookup tables.
    
    # find shortest route from source to destination
    def route(self, source, destination):
        return nx.shortest_path(graph, source = 2, destinaiton = 4)
    
    # set up routing: accumalate route and optimize it ... okiez
    def routing(self):
        for source in nodes:
            for destination in nodes:
                path = route(source, destination)
                source.add_route(destination, path)
    
    def setup(self, cubesats, groundstations):
        # assign static gound stations and model link failure and handoffs ... don't do dynamic ground stations?
        # for each cubesat ... assign ground station
        pass
    
    def nextHop(self, source, destination):
        route = nx.shortest_path(self.graph, source, destination)
        return route[1]
        
    def start(self):
        pass
    
    def draw(self):
        nx.draw(self.graph)
        
    def save(self, graph_name = "graph.png"):
        pyplot.savefig(graph_name)
           
    def show(self):
        pyplot.show()


import unittest
import random

class TestSequenceFunctions(unittest.TestCase):
    def setUp(self):
        self.seq = range(10)
        
    def test_shuffle(self):
        # make sure the shuffled sequence does not lose any elements
        random.shuffle(self.seq)
        self.seq.sort()
        self.assertEqual(self.seq, range(10))
        # should raise an exception for an immutable sequence
        self.assertRaises(TypeError, random.shuffle, (1,2,3))

    def test_choice(self):
        element = random.choice(self.seq)
        self.assertTrue(element in self.seq)

    def test_sample(self):
        with self.assertRaises(ValueError):
            random.sample(self.seq, 20)
        for element in random.sample(self.seq, 5):
            self.assertTrue(element in self.seq)

	def tearDown(self):
		pass


if __name__ == '__main__':
    unittest.main()
