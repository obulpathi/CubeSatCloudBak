#!/usr/bin/env python

from master import Master
from slave import Slave
import atom
import networkx as nx
from matplotlib import pyplot as plt

task = 1000000000
num_of_slaves = 20

# create slaves
slaves = []
for i in range(num_of_slaves):
	slaves.append(Slave(i))

# create master
master = Master(task, slaves)

nodes = [master]
nodes.extend(slaves)

# create topology
cluster = atom.Atom21(nodes)

nx.draw(cluster)
plt.show()

for node in nodes:
	node.init(cluster, nodes)
	node.print_routing_table()
	
print "ATOM created"

nx.draw(cluster)
plt.show()

# until done ... keep running
while master.task >= 0:
	master.step()
