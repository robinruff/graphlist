from graphlist import GraphList, HDFGraphList
import networkx as nx
import numpy as np
import h5py

graph1 = nx.MultiDiGraph()
graph1.add_node(0, attr1=np.array([1,2,3]), attr2=np.array([1.1, 2.2]))
graph1.add_node(1, attr1=np.array([4,5,6]), attr2=np.array([3.3, 4.4]))
graph1.add_node(2, attr1=np.array([7,8,9]), attr2=np.array([5.5, 6.6]))
graph1.add_edge(0, 1, attr1=3.4)
graph1.add_edge(0, 2, attr1=7.2)
setattr(graph1, 'global_attr', True)

graph2 = nx.MultiDiGraph()
graph2.add_node(0, attr1=np.array([9,8,7]), attr2=np.array([7.7, 8.8]))
graph2.add_node(1, attr1=np.array([6,5,4]), attr2=np.array([9.9, 0.0]))
graph2.add_edge(0, 1, attr1=5.9)
setattr(graph2, 'global_attr', False)


graphs = GraphList.from_nx_graphs([graph1, graph2, graph2, graph1],
                                  node_attribute_names=['attr1', 'attr2'],
                                  edge_attribute_names=['attr1'],
                                  graph_attribute_names=['global_attr'])

# Printing graphs tells you all the node, edge and graph attributes, their shapes and dtype:
graphs

# Output:
# > GraphTuple containing 4 graphs.
# > 
# > Node Attributes:
# > 
# >         - attr1
# >                 shape: (3,)
# >                 dtype: int64
# >         - attr2
# >                 shape: (2,)
# >                 dtype: <U5
# > 
# > Edge Attributes:
# > 
# >         - attr1
# >                 shape: ()
# >                 dtype: float64
# > 
# > Graph Attributes:
# > 
# >         - global_attr
# >                 shape: ()
# >                 dtype: bool

# For each graph the number of edges and nodes are stored:
graphs.num_nodes
# array([3, 2, 2, 3])
graphs.num_edges
# array([2, 1, 1, 2])

# The graph topology is stored in an edge list:
graphs.edge_indices
# array([[0, 1],
#        [0, 2],
#        [0, 1],
#        [0, 1],
#        [0, 1],
#        [0, 2]])

# GraphLists can be indexed with integers, lists of integers or slices:
graphs[[0,3]]
graphs[2]
graphs[:2]
graphs[-2:]

# Get the data with
graphs[-2:].graph_attributes['global_attr']
# array([False,  True])
graphs[3].node_attributes['attr1']
# array([[1, 2, 3],   attr1 for node 0
#        [4, 5, 6],   attr1 for node 1
#        [7, 8, 9]])  attr1 for node 2
graphs[0].edge_attributes['attr1']
# array([5.9])


# You can also persist graphs to the disk with HDF5:

with h5py.File('/tmp/test_graphs.h5', 'a') as f:
    hdf_graphs = HDFGraphList.from_graphlist(f, graphs)
    # HDFGraphList behaves just like GraphList, but the data is stored on disk.
    out = hdf_graphs[3].node_attributes['attr1']
    hdf_graphs.append_graphlist(graphs)

with h5py.File('/tmp/test_graphs.h5', 'r') as f:
    # load from file
    hdf_graphs = HDFGraphList(f)
    # Only read a subset into memory
    memory_graphs = hdf_graphs[-4:]

# memory_graphs is still available when file is closed


def get_random_graph():
    graph = nx.MultiDiGraph()
    for i in range(np.random.randint(10)):
        graph.add_node(i, attr1=np.random.random((3,4)), attr2=np.random.rand())
    for i in range(graph.number_of_nodes()):
        for j in range(graph.number_of_nodes()):
            if np.random.choice([True, False]):
                graph.add_edge(i, j, attr1=np.random.rand())
    return graph

