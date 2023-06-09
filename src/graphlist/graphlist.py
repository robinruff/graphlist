import numpy as np
from typing import List
from functools import cached_property
from networkx import MultiDiGraph
from typing import Dict
import logging


class GraphList:
    """
    Class to efficiently store homogeneous graph datasets.

    Inspired by jraphs GraphsTuple implementation (https://github.com/deepmind/jraph/blob/master/jraph/_src/graph.py).
    """

    def __init__(
        self,
        num_nodes: np.ndarray,
        num_edges: np.ndarray,
        edge_indices: np.ndarray,
        node_attributes: Dict[str, np.ndarray],
        edge_attributes: Dict[str, np.ndarray],
        graph_attributes: Dict[str, np.ndarray],
    ):
        """Initializes GraphTuple.
        Args:
            num_nodes (np.ndarray): Number of nodes in each graph. Shape: (num_graphs).
            num_edges (np.ndarray): Number of edges in each graph. Shape: (num_graphs).
            edge_indices (np.ndarray): Edge indices, which describe graph topology. Shape: (num_edges, 2)
            node_attributes (dict[str, np.ndarray]): Dictionary of node attributes.
                Each key is the label of the corresponding numpy array.
                Each numpy array should be of shape (num_nodes, ...).
            edge_attributes (dict[str, np.ndarray]): Dictionary of edge attributes.
                Each key is the label of the corresponding numpy array.
                Each numpy array should be of shape (num_edges, ...).
            graph_attributes (dict[str, np.ndarray]): Dictionary of global graph attributes.
                Each key is the label of the corresponding numpy array.
                Each numpy array should be of shape (num_graphs, ...).
        """
        self.num_nodes: np.ndarray = num_nodes
        self.num_edges: np.ndarray = num_edges
        self.edge_indices: np.ndarray = edge_indices
        self.node_attributes: dict = node_attributes
        self.edge_attributes: dict = edge_attributes
        self.graph_attributes: dict = graph_attributes
        self.node_attribute_names = list(node_attributes.keys())
        self.edge_attribute_names = list(edge_attributes.keys())
        self.graph_attribute_names = list(graph_attributes.keys())

    @cached_property
    def node_starts(self):
        node_starts = np.roll(np.cumsum(self.num_nodes), 1)
        node_starts[0] = 0
        return node_starts

    @cached_property
    def edge_starts(self):
        edge_starts = np.roll(np.cumsum(self.num_edges), 1)
        edge_starts[0] = 0
        return edge_starts

    @staticmethod
    def from_nx_graphs(
        graphs: List[MultiDiGraph],
        node_attribute_names=[],
        edge_attribute_names=[],
        graph_attribute_names=[],
    ):
        """Converts a list of networkx graphs to a GraphTuple dataset.
        Args:
            graphs (List[MultiDiGraph]): The networkx graphs to convert to a GraphTuple dataset.
            node_attribute_names (list, optional): Keys of the node attributes.
                The nodes of the networkx graph must have this key as node property.
                Defaults to [].
            edge_attribute_names (list, optional): Keys of the node attributes.
                The edges of the networkx graph must have this key as node property.
                Defaults to [].
            graph_attribute_names (list, optional): Keys of the graph attributes.
                The networkx graph must have this key as attribute name.
                Defaults to [].
        Returns:
            GraphTuple: The converted networkx graphs as GraphTuple.
        """
        num_nodes = np.array([g.number_of_nodes() for g in graphs])
        num_edges = np.array([g.number_of_edges() for g in graphs])
        node_starts = np.roll(np.cumsum(num_nodes), 1)
        node_starts[0] = 0
        edge_starts = np.roll(np.cumsum(num_edges), 1)
        edge_starts[0] = 0

        node_attributes = dict()
        edge_attributes = dict()
        graph_attributes = dict()
        edge_indices = np.zeros(shape=(num_edges.sum(), 2), dtype=int)

        for node_attr in node_attribute_names:
            if node_starts[-1] == 0:
                logging.warn("No nodes in all graphs.")
                break
            peek = np.array(next(
                iter(graphs[np.argwhere(num_nodes > 0)[0, 0]].nodes(data=node_attr)))[1])
            shape = (num_nodes.sum(),) + peek.shape
            dtype = peek.dtype
            node_attributes[node_attr] = np.zeros(shape=shape, dtype=dtype)

        for edge_attr in edge_attribute_names:
            if edge_starts[-1] == 0:
                logging.warn("No edges in all graphs.")
                break
            peek = np.array(next(
                iter(graphs[np.argwhere(num_edges > 0)[0, 0]].edges(data=edge_attr)))[2])
            shape = (num_edges.sum(),) + peek.shape
            dtype = peek.dtype
            edge_attributes[edge_attr] = np.zeros(shape=shape, dtype=dtype)

        for graph_attr in graph_attribute_names:
            peek = np.array(getattr(graphs[0], graph_attr))
            shape = (num_nodes.shape[0],) + peek.shape
            dtype = peek.dtype
            graph_attributes[graph_attr] = np.zeros(shape=shape, dtype=dtype)

        i_n = 0
        i_e = 0
        i_g = 0
        for g in graphs:
            node_numbers = {n: i for i, n in enumerate(g.nodes)}
            for node in g.nodes(data=True):
                for node_attr in node_attribute_names:
                    node_attributes[node_attr][i_n] = np.array(node[1][node_attr])
                i_n += 1
            for edge in g.edges(data=True):
                for edge_attr in edge_attribute_names:
                    edge_attributes[edge_attr][i_e] = np.array(edge[2][edge_attr])
                edge_indices[i_e] = np.array(
                    [node_numbers[edge[0]], node_numbers[edge[1]]], dtype=int
                )
                i_e += 1

            for graph_attr in graph_attribute_names:
                graph_attributes[graph_attr][i_g] = np.array(getattr(g, graph_attr))
            i_g += 1

        return GraphList(
            num_nodes,
            num_edges,
            edge_indices,
            node_attributes,
            edge_attributes,
            graph_attributes,
        )

    def to_nx_graphs(self) -> List[MultiDiGraph]:
        """Converts a GraphTuple to a list of networkx graphs.
        Returns:
            List[MultiDiGraph]: A list of networkx graphs.
        """
        nx_graphs = []
        for g in self:
            nx_graph = MultiDiGraph()
            nodes = []
            node_attributes = g.node_attributes.keys()
            for i in range(g.num_nodes[0]):
                attr = {
                    node_attribute: g.node_attributes[node_attribute][i]
                    for node_attribute in node_attributes
                }
                nodes.append((i, attr))
            nx_graph.add_nodes_from(nodes)
            edges = []
            edge_attributes = g.edge_attributes.keys()
            for i in range(g.num_edges[0]):
                attr = {
                    edge_attribute: g.edge_attributes[edge_attribute][i]
                    for edge_attribute in edge_attributes
                }
                node1 = g.edge_indices[i][0]
                node2 = g.edge_indices[i][1]
                edges.append((node1, node2, attr))
            nx_graph.add_edges_from(edges)
            for graph_attribute, v in g.graph_attributes.items():
                setattr(nx_graph, graph_attribute, v[0])
            nx_graphs.append(nx_graph)
        return nx_graphs

    def _get_subslice(self, indices: List[int]):
        num_graphs = len(indices)
        num_nodes = self.num_nodes[indices]
        num_edges = self.num_edges[indices]
        node_starts = np.roll(np.cumsum(num_nodes), 1)
        node_starts[0] = 0
        edge_starts = np.roll(np.cumsum(num_edges), 1)
        edge_starts[0] = 0

        edge_indices = np.zeros(shape=(num_edges.sum(), 2), dtype=int)

        graph_dict = {
            "num_nodes": num_nodes,
            "num_edges": num_edges,
            "node_attributes": {},
            "edge_attributes": {},
            "graph_attributes": {},
            "edge_indices": edge_indices,
        }

        for node_attr in self.node_attribute_names:
            shape = (num_nodes.sum(),) + self.node_attributes[node_attr].shape[1:]
            dtype = self.node_attributes[node_attr].dtype
            graph_dict["node_attributes"][node_attr] = np.zeros(
                shape=shape, dtype=dtype
            )

        for edge_attr in self.edge_attribute_names:
            shape = (num_edges.sum(),) + self.edge_attributes[edge_attr].shape[1:]
            dtype = self.edge_attributes[edge_attr].dtype
            graph_dict["edge_attributes"][edge_attr] = np.zeros(
                shape=shape, dtype=dtype
            )

        for graph_attr in self.graph_attribute_names:
            shape = (num_graphs,) + self.graph_attributes[graph_attr].shape[1:]
            dtype = self.graph_attributes[graph_attr].dtype
            graph_dict["graph_attributes"][graph_attr] = np.zeros(
                shape=shape, dtype=dtype
            )

        for i in range(num_graphs):

            for node_attr in self.node_attribute_names:
                graph_dict["node_attributes"][node_attr][
                    node_starts[i] : node_starts[i] + num_nodes[i]
                ] = self.node_attributes[node_attr][
                    self.node_starts[indices[i]] : self.node_starts[indices[i]]
                    + self.num_nodes[indices[i]]
                ]

            for edge_attr in self.edge_attribute_names:
                graph_dict["edge_attributes"][edge_attr][
                    edge_starts[i] : edge_starts[i] + num_edges[i]
                ] = self.edge_attributes[edge_attr][
                    self.edge_starts[indices[i]] : self.edge_starts[indices[i]]
                    + self.num_edges[indices[i]]
                ]

            for graph_attr in self.graph_attribute_names:
                graph_dict["graph_attributes"][graph_attr][i] = self.graph_attributes[
                    graph_attr
                ][indices[i]]

            graph_dict["edge_indices"][
                edge_starts[i] : edge_starts[i] + num_edges[i]
            ] = self.edge_indices[
                self.edge_starts[indices[i]] : self.edge_starts[indices[i]]
                + self.num_edges[indices[i]]
            ]

        graph_tuple_slice = GraphList(
            graph_dict["num_nodes"],
            graph_dict["num_edges"],
            graph_dict["edge_indices"],
            graph_dict["node_attributes"],
            graph_dict["edge_attributes"],
            graph_dict["graph_attributes"],
        )
        return graph_tuple_slice

    def __len__(self):
        return self.num_nodes[:].shape[0]

    def __getitem__(self, index):
        if isinstance(index, int):
            return self.__getitem__([index])
        elif isinstance(index, slice):
            start = 0 if index.start is None else index.start
            stop = len(self) if index.stop is None else index.stop
            if start < 0:
                start = len(self) + start
            if stop < 0:
                stop = len(self) + stop
            if stop > len(self):
                stop = len(self)
            if start >= stop:
                return None
            return self.__getitem__(np.arange(start, stop, index.step))
        elif isinstance(index, (list, np.ndarray)):
            return self._get_subslice(index)

    def __repr__(self):
        header_info = f"GraphTuple containing {len(self)} graphs."
        node_attributes_info = f"Node Attributes:\n\n"
        for k in self.node_attributes.keys():
            node_attributes_info += f"\t- {k}\n\t\tshape: {self.node_attributes[k].shape[1:]}\n\t\tdtype: {self.node_attributes[k].dtype}\n"
        edge_attributes_info = f"Edge Attributes:\n\n"
        for k in self.edge_attributes.keys():
            edge_attributes_info += f"\t- {k}\n\t\tshape: {self.edge_attributes[k].shape[1:]}\n\t\tdtype: {self.edge_attributes[k].dtype}\n"
        graph_attributes_info = f"Graph Attributes:\n\n"
        for k in self.graph_attributes.keys():
            graph_attributes_info += f"\t- {k}\n\t\tshape: {self.graph_attributes[k].shape[1:]}\n\t\tdtype: {self.graph_attributes[k].dtype}\n"
        repr = (
            header_info
            + "\n\n"
            + node_attributes_info
            + "\n"
            + edge_attributes_info
            + "\n"
            + graph_attributes_info
        )
        return repr

