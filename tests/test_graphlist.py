import unittest
import numpy as np
import networkx as nx
from graphlist import GraphList

class TestGraphList(unittest.TestCase):

    def test_graphlist(self):
        num_graphs = 50
        nx_graphs = self.generate_random_graphs(num_graphs)
        graphs = GraphList.from_nx_graphs(nx_graphs,
                                 node_attribute_names=['node_attribute1', 'attribute'],
                                 edge_attribute_names=['edge_attribute1', 'attribute'],
                                 graph_attribute_names=['attribute', 'graph_attribute'])

        for graph_idx, graph in enumerate(nx_graphs):
            for node_idx, data in graph.nodes(data=True):
                self.assertTrue(np.all(
                    data['attribute'] ==
                    graphs[graph_idx].node_attributes['attribute'][node_idx]))
                self.assertTrue(np.all(
                    data['node_attribute1'] ==
                    graphs[graph_idx].node_attributes['node_attribute1'][node_idx]))
            for edge_idx, (src, dest, data) in enumerate(graph.edges(data=True)):
                edge_indices = graphs[graph_idx].edge_indices[edge_idx]
                self.assertTrue(src == edge_indices[0])
                self.assertTrue(dest == edge_indices[1])
                self.assertTrue(np.all(
                    data['attribute'] ==
                    graphs[graph_idx].edge_attributes['attribute'][edge_idx]))
                self.assertTrue(np.all(
                    data['edge_attribute1'] ==
                    graphs[graph_idx].edge_attributes['edge_attribute1'][edge_idx]))
            self.assertTrue(np.all(graph.attribute == graphs[graph_idx].graph_attributes['attribute']))
            self.assertTrue(np.all(graph.graph_attribute == graphs[graph_idx].graph_attributes['graph_attribute']))

    @staticmethod
    def generate_random_graphs(number_of_graphs = 50):
        # Generate 50 random graphs with networkx
        nx_graphs = [nx.fast_gnp_random_graph(np.random.randint(100), np.random.rand()) for _ in range(number_of_graphs)]
        # Populate graphs with random attributes
        for nx_graph in nx_graphs:
            for node, data in nx_graph.nodes(data=True):
                data['node_attribute1'] = np.random.random(5)
                data['node_attribute2'] = np.random.random((3,3))
                data['node_attribute3'] = np.random.randint(100)
                data['attribute'] = np.random.randint(100)
            for src, dest, data in nx_graph.edges(data=True):
                data['edge_attribute1'] = np.random.random(7)
                data['attribute'] = np.random.randint(100)
            setattr(nx_graph, 'graph_attribute', np.random.random(1))
            setattr(nx_graph, 'attribute', np.random.randint(100))
        return nx_graphs

if __name__ == '__main__':
    unittest.main()
