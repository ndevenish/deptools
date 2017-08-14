#!/usr/bin/env python
# coding: utf-8

"""
Determine the python dependencies for a tbx-like distribution.

This takes a path to a tbx-distribution (the modules directory), and makes a 
list of every 'module' - that is, all folders in that path and the 'cctbx_project'
subdirectory that match a predefined list. Every python file in each 'module'
is then scanned for import statements, and each import that matches another
module is counted as a dependency.

Note that this doesn't attempt to determine whether an import statement is
conditional - it will find the import regardless, so the dependency graph is
for *all possible* dependencies. Modules imported through the __import__
statement currently won't be discovered.

Usage:
  scan_pythondeps [options] [-o <OUTPUT>] <module_path> 

Options:
  -o <OUTPUT>   Write a yaml dependency graph to a file instead of stdout
"""

from __future__ import print_function
import os, sys
import ast
import yaml
from docopt import docopt

# A list of all valid module names. Used to filter out external dependencies and
# other stray folders that could pollute the names
module_names = { "annlib", "annlib_adaptbx", "boost_adaptbx", "cbflib", "cbflib_adaptbx", 
            "ccp4io", "ccp4io_adaptbx", "cctbx", "chiltbx", "clipper", "clipper_adaptbx", 
            "cma_es", "cootbx", "crys3d", "cudatbx", "cxi_user", "dials", "dxtbx", "fable", 
            "fftw3tbx", "gltbx", "gui_resources", "iota", "iotbx", "libtbx", "mmtbx", "omptbx", 
            "prime", "rstbx", "scitbx", "simtbx", "smtbx", "sphinx", "spotfinder", "tbxx", 
            "tntbx", "ucif", "wxtbx", "xfel", "xia2"}

read_module_names = {"libtbx"}

class ImportVisitor(ast.NodeVisitor):
  """Visit and list all import nodes in a python AST"""
  def __init__(self, *args, **kwargs):
    self._imports = set()
    # self._cond_imports = set()
    # self._if_nodes = set()
    # self._import_nodes = set()
    super(ImportVisitor, self).__init__(*args, **kwargs)

  # # If(expr test, stmt* body, stmt* orelse)
  # def visit_If(self, node):
  #   v2 = ImportVisitor()
  #   v2.filename = self.filename
  #   for stmt in node.body:
  #     v2.visit(stmt)
  #   for stmt in node.orelse:
  #     v2.visit(stmt)
  #   self._cond_imports |= v2._imports | v2._cond_imports
  #   self._if_nodes |= v2._import_nodes

  def visit_Import(self, node):
    # if node in self._if_nodes:
    #   print("node already visited by another iterator")
    # self._import_nodes.add(node)
    self._imports |= {alias.name for alias in node.names}

  def visit_ImportFrom(self, node):
    # if node in self._if_nodes:
    #   print("node already visited by another iterator")
    # self._import_nodes.add(node)
    self._imports.add(node.module)

  @classmethod
  def visit_path(cls, pathname):
    all_includes = set()
    # all_opts = set()
    if os.path.isdir(pathname):
      for path, dirs, files in os.walk(pathname):
        for filename in [x for x in files if x.endswith(".py")]:
          # print(filename + ":")
          tree = ast.parse(open(os.path.join(path, filename)).read(), filename)
          v = cls()
          # v.filename = filename
          v.visit(tree)
          all_includes |= v._imports
          # all_opts |= v._cond_imports
    else:
      tree = ast.parse(open(filename).read(), filename)
      v = cls()
      v.visit(tree)
    return all_includes

# options = {
#   "<module_path>": ".",
#   "-o": None
# }
options = docopt(__doc__)
dest_dir = options["<module_path>"]

# Search for all modules by looking in the provided directory and matching to known module names
mod_paths = {x: x for x in os.listdir(dest_dir) if os.path.isdir(os.path.join(dest_dir, x)) and x in module_names}
mod_paths.update({x: os.path.join(dest_dir, "cctbx_project", x) for x in os.listdir(os.path.join(dest_dir, "cctbx_project")) if os.path.isdir(os.path.join(dest_dir, "cctbx_project", x)) and x in module_names})

mod_deps = {}

for module, path in sorted(mod_paths.items()):
  print("Scanning {} for dependencies".format(module), file=sys.stderr)
  all_includes = ImportVisitor.visit_path(path)
  # print("Incs: ", all_includes)
  # print()
  # print("Optionals: ", opts)
  deps = set()
  for potential_dep in all_includes:
    root_name = potential_dep.split(".")[0]
    if root_name in module_names and not root_name == module:
      deps.add(root_name)
  # Don't give entries for modules without any python dependencies
  if deps:
    mod_deps[module] = list(deps)

if options["-o"]:
  with open(options["-o"], "wt") as f:
    yaml.dump(mod_deps, stream=f)
else:
  print(yaml.dump(mod_deps))

