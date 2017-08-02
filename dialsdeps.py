#!/usr/bin/env python3

import os
import yaml
from deptools import DepParser

# The path used for absolute files in the targetmap
TARGETMAP_ROOT="/Users/nickd/dials/dist/modules"
BUILD_DIR="/Users/nickd/dials/prep/_build"
SOURCE_DIR="/Users/nickd/dials/prep"

# Sanity check against things going wrong
VALID_MODULES = {'annlib', 'smtbx', 'boost_adaptbx', 'scitbx', 'xfel',
'spotfinder', 'chiltbx', 'dxtbx', 'iotbx', 'gltbx', 'cbflib_adaptbx', 'fable',
'simtbx', 'cctbx', 'annlib_adaptbx', 'mmtbx', 'omptbx', 'rstbx', 'ccp4io',
'cma_es', 'boost', 'xia2', 'ccp4io_adaptbx', 'prime',
'cbflib', 'dials', 'ucif', 'gui_resources'}

def module_from_path(path):
  opath = path
  # Remove the leading path
  if path.startswith(BUILD_DIR):
    path = path[len(BUILD_DIR)+1:]
  if path.startswith(SOURCE_DIR):
    path = path[len(SOURCE_DIR)+1:]

  assert not os.path.isabs(path), "Path {} should not be outside of distribution".format(path)

  if path.startswith("cctbx_project"):
    # this splitting is bad, except we know with our data no embedded /
    module = path.split(os.sep)[1]
  else:
    module = path.split(os.sep)[0]

  assert module in VALID_MODULES, "No module: {} (from {})".format(module, opath)
  return module

# Open the target map file
targets = yaml.load(open("targetmap.yaml"))

# Invert this to map source paths to target, module
module_mismatch = set()
source_targets = {}
source_modules = {}
for target, data in targets.items():
  for source in data["sources"]:
    if source.startswith(TARGETMAP_ROOT):
      source = source[len(TARGETMAP_ROOT)+1:]
    if source in source_targets:
      print ("Warning: More than one target for source {}; {}".format(source, [target, source_targets[source]]))
      continue
    if source in source_modules:
      print("Warning: more than one module for source {}: {}".format(source, [data["module"], source_modules[source]]))
      continue
    source_targets[source] = target
    source_modules[source] = data["module"]
    source_modules[source] = module_from_path(source)
    # Attempt to extract the module from name and check this matches
    if source_modules[source] != data["module"]:
      srcmod = source_modules[source]
      tgtmod = data["module"]
      if not (srcmod, tgtmod) in module_mismatch:
        print("Source/target module mismatch for at least {}: {} != {}".format(source, source_modules[source], data["module"]))
        module_mismatch.add((srcmod, tgtmod))

# Get a list of all modules involved in the build
modules = {x["module"] for x in targets.values()}
assert not "." in modules, "Badly classified targets"
print("All modules: {}".format(", ".join(modules)))

# Load the dependency graph
depgraph = DepParser.fromdict(yaml.load(open("depdata.yaml")))
# Clean it up
depgraph.remove_root(BUILD_DIR+"/")
depgraph.remove_root(SOURCE_DIR+"/")

# Assign a target, module for each source file in these
all_sources = set(source_targets.keys())
for source in depgraph.source_files:
  source.module = module_from_path(source.name)

  # Warn if this source wasn't listed as having a target/module
  if not source.name in all_sources:
    print("Warning: {} not listed in targets file".format(source.name))
    source.target = None
  else:
    source.target = source_targets[source.name]
  
