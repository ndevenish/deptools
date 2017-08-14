#!/usr/bin/env python3
# coding: utf-8

"""Draw several dependency sources as a single, unified graph.

Usage:
  draw_graph.py [options] --python=<PY_DEPS> [--cxx=<CXX_DEPS>]
  draw_graph.py [options] [--python=<PY_DEPS>] --cxx=<CXX_DEPS>

Options:
  -o OUTPUT   Where to write the output graphviz file to [default: out.gv]
"""

import yaml
import pygraphviz as pgv
from docopt import docopt

options = docopt(__doc__)

print(options)

python_deps = {}
python_optional_deps = {}
cxx_deps = {}
cxx_libs = {}

if options["--python"]:
  python_deps = yaml.load(open(options["--python"]))
  # Separate out the optional dependencies
  python_optional_deps = python_deps.get("_optional", None)
  if python_optional_deps is not None:
    del python_deps["_optional"]

if options["--cxx"]:
  cxx_deps = yaml.load(open(options["--cxx"]))
  cxx_libs = cxx_deps.get("_library", None)
  if cxx_libs is not None:
    del cxx_deps["_library"]

# Exclude optional python dependencies that don't exist as c++ targets
all_nodenames = set(python_deps.keys()) | set(cxx_deps.keys()) | set(python_optional_deps.keys())

# Valid module names - e.g. use this to filter
valid_modnames = {'annlib', 'annlib_adaptbx', 'boost_adaptbx', 'cbflib', 'cbflib_adaptbx', 
                  'ccp4io', 'ccp4io_adaptbx', 'cctbx', 'chiltbx', 'clipper', 
                  'clipper_adaptbx', 'cma_es', 'cootbx', 'crys3d', 'cudatbx', 'cxi_user', 'dials', 
                  'dox', 'dox.sphinx', 'dxtbx', 'fable', 'fftw3tbx', 'gltbx', 'gui_resources', 
                  'iota', 'iotbx', 'libtbx', 'mmtbx', 'omptbx', 'prime', 'rstbx', 'scitbx', 
                  'scons', 'sphinx', 'simtbx', 'smtbx', 'spotfinder', 'tbxx', 'tntbx', 'ucif', 
                  'wxtbx', 'xfel', 'xia2'}
# Removed: sphinx

# Modeuls to ignore
not_modnames = {"sphinx", "libtbx", "cctbx", "scitbx", "iotbx"}

# Remove nodes that aren't in the valid list, but allow everything in the valid list
all_nodenames = (all_nodenames & valid_modnames) - not_modnames

graph = pgv.AGraph(directed=True)
for nodename in all_nodenames:
  shape = "box" if nodename in cxx_libs else "ellipse"
  all_node_deps = set(python_deps.get(nodename, [])) | set(python_optional_deps.get(nodename, [])) | set(cxx_deps.get(nodename, []))
  app = ""
  if "libtbx" in all_node_deps:
    app += "L"
  if "cctbx" in all_node_deps:
    app += "C"
  if "scitbx" in all_node_deps:
    app += "S"
  if "iotbx" in all_node_deps:
    app += "I"
  if app:
    graph.add_node(nodename, shape=shape, label=r"{}\n{}".format(nodename, app))
  else:
    graph.add_node(nodename, shape=shape)
# graph.add_nodes_from(all_nodenames)

# Add CXX edges
for node, deps in cxx_deps.items():
  if not node in all_nodenames:
    continue
  for dep in deps:
    if dep in all_nodenames:
      graph.add_edge(node, dep)

def _add_python_edges(graph, deps, cxx_deps, valid_nodenames=None, **kwargs):
  # Add python solid edges
  for node, deps in deps.items():
    # Skip nodes that aren't in the allowed list
    if valid_nodenames and not node in valid_nodenames:
      continue
    # Don't add a second connnection if we already had this
    deps = set(deps) - set(cxx_deps.get(node, []))
    for dep in deps:
      # if node == "libtbx" and dep == "sphinx":
      #   import pdb
      #   pdb.set_trace()
      if not valid_nodenames or dep in valid_nodenames:
        graph.add_edge(node, dep, **kwargs)

# graph.edge_attr["color"] = "green"
_add_python_edges(graph, python_deps, cxx_deps, valid_nodenames=all_nodenames, color="green")
_add_python_edges(graph, python_optional_deps, cxx_deps, valid_nodenames=all_nodenames, color="green", style="dashed")

# # Adding a key to the graph: Just code here for now.
  # subgraph cluster_key {
  #     label="Key";
  #     //rankdir=LR;
  #     rank=min;
      
  #     kc1[label="Interface", shape="ellipse"];
  #     kc2[label="Compiled Library", shape="box"];
  #     kc3[label="Extra Dependencies\nL = libtbx\nC = cctbx\nS = scitbx", shape="box"];

  #     pynd1[shape="point"];
  #     pynd2[shape="point"];
  #     pynd1->pynd2[color="green", label="Python"];

  #     cxxnd1[shape="point"];
  #     cxxnd2[shape="point"];
  #     cxxnd1->cxxnd2[color="black", label="C++"];

  #     pyndo1[shape="point"];
  #     pyndo2[shape="point"];
  #     pyndo1->pyndo2[color="green", label="Python\nOptional/\nvia tests", style="dashed"];
  # }
graph.write(options["-o"])

