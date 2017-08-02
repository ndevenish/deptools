#!/usr/bin/env python3

from collections import defaultdict
import os
import yaml
from deptools import DepParser, SourceFile
import graphviz as gv
from pprint import pprint
import itertools

# The path used for absolute files in the targetmap
TARGETMAP_ROOT="/Users/nickd/dials/dist/modules"
BUILD_DIR="/Users/nickd/dials/prep/_build"
SOURCE_DIR="/Users/nickd/dials/prep"

# Sanity check against things going wrong
VALID_MODULES = {'annlib', 'smtbx', 'boost_adaptbx', 'scitbx', 'xfel',
'spotfinder', 'chiltbx', 'dxtbx', 'iotbx', 'gltbx', 'cbflib_adaptbx', 'fable',
'simtbx', 'cctbx', 'annlib_adaptbx', 'mmtbx', 'omptbx', 'rstbx', 'ccp4io',
'cma_es', 'boost', 'xia2', 'ccp4io_adaptbx', 'prime',
'cbflib', 'dials', 'ucif', 'gui_resources', "tbxx"}

def module_from_path(path):
  opath = path
  # Remove the leading path
  if path.startswith(BUILD_DIR):
    path = path[len(BUILD_DIR)+1:]
  if path.startswith(SOURCE_DIR):
    path = path[len(SOURCE_DIR)+1:]

  assert not os.path.isabs(path), "Path {} should not be outside of distribution".format(path)

  if path.startswith("include"):
    path = path[len("include/"):]

  if path.startswith("cctbx_project"):
    # this splitting is bad, except we know with our data no embedded /
    module = path.split(os.sep)[1]
  else:
    module = path.split(os.sep)[0]


  assert module in VALID_MODULES, "No module: {} (from {})".format(module, opath)
  return module

def _makerel(path):
  paths = list(reversed(sorted([TARGETMAP_ROOT, BUILD_DIR, SOURCE_DIR], key=lambda x: len(x))))
  for prefix in paths:
    if path.startswith(prefix):
      path = path[len(prefix)+1:]
  return path

class Target(object):
  def __init__(self, name, module, sources=None):
    self.name = name
    self.module = module
    self.sources = sources or set()
  def __repr__(self):
    return "Target('{}', '{}')".format(self.name, self.module)

def _read_targets(dictdata, depgraph):
  """Read an iterable of targets from a target dictionary"""

  # Make a source-file lookup
  source_objs = {x.name: x for x in depgraph.source_files}

  # Track module mismatches so we don't spam
  module_mismatch = set()

  # Open the target map file and convert to a list of target objects
  for targetname, data in dictdata.items():
    # We don't want to inspect building of boost. skip it.
    if data["module"] == "boost":
      continue
    # Create a target object
    target = Target(targetname, data["module"])
    # Convert each source file into a dependency graph reference
    for source_filename in data["sources"]:
      source_filename = _makerel(source_filename)
      if not source_filename in source_objs:
        print("Warning: source {} in target map file but no header lookup".format(source_filename))
        # import pdb
        # pdb.set_trace()
      source = source_objs[source_filename]

      if hasattr(source, "targets") and len(source.targets) > 0:
        print ("Warning: More than one target for source {}; {}".format(source.name, [next(iter(source.targets)).name, target.name]))
      else:
        source.targets = set()

      # Make two-way navigation between source and targets
      target.sources.add(source)
      source.targets.add(target)

      # Let's assign the source module here...
      source.module = module_from_path(source.name)
      if source.module != target.module and not (source.module, target.module) in module_mismatch:
        print("Source/target module mismatch for at least {}: {} != {}".format(source.name, source.module, target.module))
        module_mismatch.add((source.module, target.module))
    yield target

# Load the dependency graph
depgraph = DepParser.fromdict(yaml.load(open("depdata.yaml")))
depgraph.merge_multiple_source()
# Clean it up
depgraph.remove_root(BUILD_DIR+"/")
depgraph.remove_root(SOURCE_DIR+"/")

# Read the target-source mapping data. This should give every source file in the 
# dependency graph an associated target - exceptions are e.g. duplicate named
# targets. Just warn about those for now.
targets = {x.name: x for x in _read_targets(yaml.load(open("targetmap.yaml")), depgraph)}
for source in depgraph.source_files:
  if not hasattr(source, "targets") or not source.targets:
    print("Warning: Source {} has no target data. Setting to module.".format(source))
    source.module = module_from_path(source.name)
    source.targets = {source.module}

# Get a list of all modules involved in the build
modules = {x.module for x in targets.values()} | \
  {x.module for x in depgraph.source_files} | \
  {module_from_path(x.name) for x in depgraph.headers}
assert modules < VALID_MODULES, "Badly classified targets"
print("All modules: {}".format(", ".join(modules)))

# Make sure we have target objects for every module - it will take posession of headers
for module in modules:
  if not module in targets:
    targets[module] = Target(module, module)

def _accum_sources(header, visited=None):
  "Get all sources that include a header, even via other headers"
  visited = visited or set()
  visited |= {header}

  sources = set()
  for upstream in header.included - visited:
    if isinstance(upstream, SourceFile):
      sources.add(upstream)
    else:
      sources = sources | _accum_sources(upstream, visited)
  return sources

# Now, go through and assign a module to each header
for header in depgraph.headers:
  header.module = module_from_path(header.name)
  # Set the target as the module-level target - unless we change this
  header.targets = {targets[header.module]}

  # Now, any headers only included by one target, belong to that target
  including_targets = set(itertools.chain(*(x.targets for x in _accum_sources(header))))
  if len(including_targets) == 1:
    header.targets = {next(iter(including_targets))}

  next(iter(header.targets)).sources.add(header)

# Now, assign every header to it's target object

module_deps = defaultdict(set)

# Generate a header-dependence graph for modules
for target in targets.values():
  source_targets = set()
  for source in target.sources:
    # Collate the targets of all included files
    for include in source.includes:
      source_targets |= include.targets
  # No self-referencing
  source_targets -= {target}
  
  # if target.name == "dials_algorithms_spot_finding_helen_ext":
  #   import pdb
  #   pdb.set_trace()

  # Ignore this target if the only dependency is also the module name
  if source_targets == {targets[target.module]}:
    print("Skipping target {}".format(target.name))
    continue
  if source_targets:
    module_deps[target.name] |= {x.name for x in source_targets} - {target.name}

# import pdb
# pdb.set_trace()
  # module_deps[header.module] |= set(x.module for x in header.includes) - {header.module}
  # }

graph = gv.Digraph()
for module in module_deps:
  graph.node(module)

for module, deps in module_deps.items():
  for dep in deps:
    graph.edge(module, dep)

# g2 = gv.Digraph(format='svg')
# g2.node('A')
# g2.node('B')
# g2.edge('A', 'B')
# g2.render('img/g2')
with open("deps.gv", "w") as f:
  f.write(str(graph))
pprint (module_deps)
