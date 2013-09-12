import networkx as nx

nodes = range(10)
graph = nx.Graph()
for node in nodes:
    graph.add_node(node)
for nodeX, nodeY in zip(nodes[:-1], nodes[1:]):
    graph.add_edge(nodeX, nodeY)
for node in nodes[:3]:
    print nx.shortest_path(graph, node + 1, node + 3)
print nx.shortest_path(graph, 1, 2)
print nx.shortest_path(graph, 1, 1)
