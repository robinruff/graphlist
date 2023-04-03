# GraphList Datastructures

The `GraphList` class is a datastructure to efficiently store homogeneous graph data.

**What is homogeneous graph data?**

In homogeneous graph datasets all nodes, edges and graph attributes are of the same shape and type across the dataset.

In a machine learning setting (e.g. graph neural networks) this is a common restriction on the data.
The `GraphList` datastructure expoits this restriction to store data more efficiently (less python objects, less numpy arrays).

## Features of this library

* [x] Importing data from `networkx` graphs
* [x] Indexing graph datasets with...
	* [x] integer indices (`graphs[42]`)
	* [x] list of integer indices (`graphs[[3,5,7]]`)
	* [x] slices (`graphs[3:9]`)
* [x] Persisting data to disk (with HDF5)
	* [x] Writing, appending and reading from HDF5 files
	* [x] lazily read data from disk
* [ ] Dtype Support
	* [x] All common numerical values (see [numpy types](https://numpy.org/devdocs/user/basics.types.html))
	* [ ] Strings

## Examples:

See [`example_code.py`](./example_code.py)
