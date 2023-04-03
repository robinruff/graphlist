import h5py
import numpy as np
from typing import Iterable
from itertools import islice
from networkx import MultiDiGraph
from graphlist import GraphList

class HDFGraphList(GraphList):
    """A subclass of GraphList, which is able to read and write GraphList from/to the disk into HDF files."""

    def __init__(
        self,
        file: h5py.File,
        node_attribute_names=None,
        edge_attribute_names=None,
        graph_attribute_names=None,
    ):
        self.file = file
        self.num_nodes = np.array(self.file["num_nodes"])
        self.num_edges = np.array(self.file["num_edges"])
        if node_attribute_names is None:
            self.node_attribute_names = list(self.node_attributes.keys())
        else:
            self.node_attribute_names = node_attribute_names
        if edge_attribute_names is None:
            self.edge_attribute_names = list(self.edge_attributes.keys())
        else:
            self.edge_attribute_names = edge_attribute_names
        if graph_attribute_names is None:
            self.graph_attribute_names = list(self.graph_attributes.keys())
        else:
            self.graph_attribute_names = graph_attribute_names

    @staticmethod
    def from_nx_graphs(
        file: h5py.File,
        graphs: Iterable[MultiDiGraph],
        node_attribute_names=[],
        edge_attribute_names=[],
        graph_attribute_names=[],
        batch_size=100,
    ):
        graphs_generator = (g for g in graphs)
        while True:
            graphs_batch = list(islice(graphs_generator, batch_size))
            if len(graphs_batch) == 0:
                break
            graphlist_batch = GraphList.from_nx_graphs(
                graphs_batch,
                node_attribute_names=node_attribute_names,
                edge_attribute_names=edge_attribute_names,
                graph_attribute_names=graph_attribute_names,
            )
            graphlist_to_hdf(file, graphlist_batch)
        return HDFGraphList(
            file,
            node_attribute_names=node_attribute_names,
            edge_attribute_names=edge_attribute_names,
            graph_attribute_names=graph_attribute_names,
        )

    @property
    def edge_indices(self):
        return self.file["edge_indices"]

    @property
    def node_attributes(self):
        return self.file["node_attributes"]

    @property
    def edge_attributes(self):
        return self.file["edge_attributes"]

    @property
    def graph_attributes(self):
        return self.file["graph_attributes"]

    def append_graphlist(self, graphlist: GraphList):
        self._append_graphlist(self.file, graphlist)

    @staticmethod
    def from_graphlist(file: h5py.File, graphlist: GraphList):
        HDFGraphList._append_graphlist(file, graphlist)
        return HDFGraphList(file)

    @staticmethod
    def _append_graphlist(file: h5py.File, graphlist: GraphList):
        """Writes GraphList to a HDF file.
        If the HDF file exists already the GraphList are appended, otherwise the file is created.
        Beware that attributes of the existing GraphList in the file and GraphList to append
        must have the same attributes and the same type for each attribute.
        Args:
            file (h5py.File): HDF file to write to.
            graphlist (GraphList): GraphList dataset to append to the file.
        """
    
        # Check if file existed before (i.e. contains some graphlists already)
        file_exists = "num_nodes" in file.keys()
    
        if not file_exists:
            file.create_group("node_attributes", (0,))
            file.create_group("edge_attributes")
            file.create_group("graph_attributes")
            file.require_dataset("num_nodes", (0,), maxshape=(None,), dtype="i8")
            file.require_dataset("num_edges", (0,), maxshape=(None,), dtype="i8")
            file.require_dataset("edge_indices", (0, 2), maxshape=(None, 2), dtype="i8")
    
        file["num_nodes"].resize(
            file["num_nodes"].shape[0] + len(graphlist.num_nodes), axis=0
        )
        file["num_nodes"][-graphlist.num_nodes.shape[0] :] = graphlist.num_nodes
        file["num_edges"].resize(
            file["num_edges"].shape[0] + len(graphlist.num_edges), axis=0
        )
        file["num_edges"][-graphlist.num_edges.shape[0] :] = graphlist.num_edges
        file["edge_indices"].resize(
            file["edge_indices"].shape[0] + graphlist.edge_indices.shape[0], axis=0
        )
        file["edge_indices"][-graphlist.edge_indices.shape[0] :] = graphlist.edge_indices
    
        for node_attr, data in graphlist.node_attributes.items():
            if not file_exists:
                file["node_attributes"].create_dataset(
                    node_attr, data.shape, data=data, maxshape=((None,) + data.shape[1:])
                )
            else:
                file["node_attributes"][node_attr].resize(
                    file["node_attributes"][node_attr].shape[0] + data.shape[0], axis=0
                )
                file["node_attributes"][node_attr][-data.shape[0] :] = data
    
        for edge_attr, data in graphlist.edge_attributes.items():
            if not file_exists:
                file["edge_attributes"].create_dataset(
                    edge_attr, data.shape, data=data, maxshape=((None,) + data.shape[1:])
                )
            else:
                file["edge_attributes"][edge_attr].resize(
                    file["edge_attributes"][edge_attr].shape[0] + data.shape[0], axis=0
                )
                file["edge_attributes"][edge_attr][-data.shape[0] :] = data
    
        for graph_attr, data in graphlist.graph_attributes.items():
            if not file_exists:
                file["graph_attributes"].create_dataset(
                    graph_attr, data.shape, data=data, maxshape=((None,) + data.shape[1:])
                )
            else:
                file["graph_attributes"][graph_attr].resize(
                    file["graph_attributes"][graph_attr].shape[0] + data.shape[0], axis=0
                )
                file["graph_attributes"][graph_attr][-data.shape[0] :] = data
