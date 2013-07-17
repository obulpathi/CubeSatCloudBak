#! /usr/bin/env python

import math
import networkx as nx
from random import randint
from matplotlib import pyplot as plt

# random cluster
def cluster(nodes, r = 5000):
    master = nodes[0]
    slaves = nodes[1:]
    graph = nx.Graph()
    # assign positions to nodes
    master.location = [0, 0]
    for slave in slaves:
        slave.location = [randint(1, r), randint(1, r)]
    # build the graph
    for node in nodes:
        graph.add_node(node)
    # add edges here
    for nodex in nodes:
        for nodey in nodes:
            if nodex is nodey:
                continue
            if nodex.distance(nodey) < 2500:
                graph.add_edge(nodex, nodey)
    return graph

# grid topology    
def grid(nodes):
    pass

# ring topology
def ring(nodes):
    graph = nx.Graph()
    # add nodes
    for node in nodes:
        graph.add_node(node)
    previous = nodes[0]
    for next in nodes[1:]:
        graph.add_edge(previous, next)
        previous = next

# constellation topology
def constellation(nodes):
    pass
    
def atom(nodes):
    topology = "ATOM" + str(len(nodes))
    if topology == "ATOM5":
        return atom5(nodes)
    elif topology == "ATOM10":
        return atom10(nodes)
    elif topology == "ATOM15":
        return atom15(nodes)
    elif topology == "ATOM17":
        return atom17(nodes)
    elif topology == "ATOM20":
        return atom20(nodes)
    elif topology == "ATOM21":
        return atom21(nodes)
    elif topology == "ATOM25":
        return atom25(nodes)
    elif topology == "ATOM26":
        return atom26(nodes)
    else:
        # random cluster :) 
        return cluster(nodes)

# Atom 5
def atom5(nodes):
    graph = nx.Graph()
    for node in nodes:
        graph.add_node(node)
    master = nodes[0]
    nodes = nodes[1:]
    for node in nodes:
        graph.add_edge(master, node)
    return graph

# Atom 10
def atom10(nodes):
    graph = nx.Graph()
    for node in nodes:
        graph.add_node(node)
    master = nodes[0]
    nodes = nodes[1:]
    for i in range(3):
        graph.add_edge(master, nodes[i])
    parents = nodes[:3]
    nodes = nodes[3:]
    for i in range(6):
        graph.add_edge(nodes[i], parents[i/2])
    return graph

# Atom 15
def atom15(nodes):
    graph = nx.Graph()
    for node in nodes:
        graph.add_node(node)
    master = nodes[0]
    nodes = nodes[1:]
    for i in range(4):
        graph.add_edge(master, nodes[i])
    parents = nodes[:4]
    nodes = nodes[4:]
    for parent, node in zip(parents, nodes[:4]):
        graph.add_edge(parent, node)
    for parent, node in zip(parents, nodes[4:8]):
        graph.add_edge(parent, node)
    graph.add_edge(parents[0], nodes[-2])
    graph.add_edge(parents[2], nodes[-1])
    return graph
    
# atom 17
def atom17(nodes):
    graph = nx.Graph()
    for node in nodes:
        graph.add_node(node)
    master = nodes[0]
    nodes = nodes[1:]
    for i in range(4):
        graph.add_edge(master, nodes[i])
    parents = nodes[:4]
    nodes = nodes[4:]
    for i in range(12):
        graph.add_edge(parents[i/3], nodes[i])
    return graph

# atom 20
def atom20(nodes):
    graph = nx.Graph()
    for node in nodes:
        graph.add_node(node)
    master = nodes[0]
    nodes = nodes[1:]
    for i in range(4):
        graph.add_edge(master, nodes[i])
    parents = nodes[:4]
    nodes = nodes[4:]
    for parent, node in zip(parents, nodes[:4]):
        graph.add_edge(parent, node)
    for parent, node in zip(parents, nodes[4:8]):
        graph.add_edge(parent, node)
    for parent, node in zip(parents, nodes[8:12]):
        graph.add_edge(parent, node)
    graph.add_edge(parents[0], nodes[-3])
    graph.add_edge(parents[1], nodes[-2])
    graph.add_edge(parents[2], nodes[-1])
    return graph

# atom 21   
def atom21(nodes):
    graph = nx.Graph()
    for node in nodes:
        graph.add_node(node)
    master = nodes[0]
    nodes = nodes[1:]
    for i in range(4):
        graph.add_edge(master, nodes[i])
    parents = nodes[:4]
    nodes = nodes[4:]
    for i in range(16):
        graph.add_edge(parents[i/4], nodes[i])
    return graph

# atom 25
def atom25(nodes):
    graph = nx.Graph()
    for node in nodes:
        graph.add_node(node)
    master = nodes[0]
    nodes = nodes[1:]
    for i in range(5):
        graph.add_edge(master, nodes[i])
    parents = nodes[:5]
    nodes = nodes[5:]
    for i in range(15):
        graph.add_edge(nodes[i], parents[i%5])
    for parent, node in zip(parents, nodes[-4:]):
        graph.add_edge(parent, node)
    return graph

# atom26
def atom26(nodes):
    graph = nx.Graph()
    for node in nodes:
        graph.add_node(node)
    master = nodes[0]
    nodes = nodes[1:]
    for i in range(5):
        graph.add_edge(master, nodes[i])
    parents = nodes[:5]
    nodes = nodes[5:]
    for i in range(20):
        graph.add_edge(parents[i/4], nodes[i])
    return graph
    
if __name__ == "__main__":
    topologies = ["ATOM5", "ATOM10", "ATOM15", "ATOM17", "ATOM20", "ATOM25", "ATOM26"]
    for topology in topologies:
        if topology == "ATOM5":
            graph = atom5(range(5))
        elif topology == "ATOM10":
            graph = atom10(range(10))
        elif topology == "ATOM15":
            graph = atom15(range(15))
        elif topology == "ATOM17":
            graph = atom17(range(17))
        elif topology == "ATOM20":
            graph = atom20(range(20))
        elif topology == "ATOM25":
            graph = atom25(range(25))
        elif topology == "ATOM26":
            graph = atom26(range(26))
        else:
            graph = cluster(range(randint(5, 25))) 
        nx.draw(graph)
        plt.show()
