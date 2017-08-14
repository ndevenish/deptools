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
# other stray folders that could pollute the names. Taken from union of dials and 
# phenix builders. This includes non tbx-'module' dependencies that are internal.
module_names = {'amber_adaptbx', 'annlib', 'annlib_adaptbx', 'boost_adaptbx', 
                'cbflib', 'cbflib_adaptbx', 'ccp4io', 'ccp4io_adaptbx', 'cctbx', 
                'chem_data', 'chiltbx', 'clipper', 'clipper_adaptbx', 
                'cma_es', 'cootbx', 'crys3d', 'cudatbx', 'cxi_user', 'dials', 
                'dials_regression', 'dxtbx', 'elbow', 'fable', 'fftw3tbx', 'gltbx', 
                'gui_resources', 'iota', 'iotbx', 'king', 'ksdssp', 'labelit', 
                'libtbx', 'mmtbx', 'muscle', 'omptbx', 'opt_resources', 'phaser', 
                'phaser_regression', 'phenix', 'phenix_examples', 'phenix_html', 
                'phenix_regression', 'Plex', 'prime', 'probe', 'pulchra', 'PyQuante', 
                'reduce', 'reel', 'rstbx', 'scitbx', 'scons', 'simtbx', 'smtbx', 
                'solve_resolve', 'sphinx', 'spotfinder', 'suitename', 'tbxx', 'tntbx', 
                'ucif', 'wxtbx', 'xfel', 'xia2', 'xia2_regression'}

class ImportVisitor(ast.NodeVisitor):
  """Visit and list all import nodes in a python AST"""
  def __init__(self, *args, **kwargs):
    self._imports = set()
    self._conditional_imports = set()
    super(ImportVisitor, self).__init__(*args, **kwargs)

  # # If(expr test, stmt* body, stmt* orelse)
  def visit_If(self, node):
    v2 = ImportVisitor()
    for stmt in node.body:
      v2.visit(stmt)
    for stmt in node.orelse:
      v2.visit(stmt)
    self._conditional_imports |= v2._imports | v2._conditional_imports

  def visit_Import(self, node):
    self._imports |= {alias.name for alias in node.names}

  def visit_ImportFrom(self, node):
    self._imports.add(node.module)


   # TryExcept(stmt* body, excepthandler* handlers, stmt* orelse)
   #        | TryFinally(stmt* body, stmt* finalbody)
  def visit_TryExcept(self, node):
    v2 = ImportVisitor()
    for stmt in node.body:
      v2.visit(stmt)
    # Assume that everything inside this try-except is protected
    self._conditional_imports |= v2._imports | v2._conditional_imports

  @classmethod
  def visit_path(cls, pathname):
    """Visit a directory and inspect python files for all imports.

    Returns a tuple of (imports, conditional_imports), where a conditional
    import is counted as any import wrapped in an 'if' statement, or a 'try'
    block. No attempt is made to resolve the conditions of the 'if' or exceptions
    handled by the try block.
    """
    definite_imports = set()
    protected_imports = set()

    assert os.path.isdir(pathname), "{} is not a dir".format(pathname)
    # Walk every (.py) file in this directory
    for path, dirs, files in os.walk(pathname):
      for filename in [x for x in files if x.endswith(".py")]:
        tree = ast.parse(open(os.path.join(path, filename)).read(), filename)
        v = cls()
        v.visit(tree)
        # Do a dumb 'filter' on files that look like tests and mark the imports optional
        if filename.startswith("tst_") or filename.startswith("test_"):
          protected_imports |= v._conditional_imports | v._imports
        else:
          definite_imports |= v._imports
          protected_imports |= v._conditional_imports

    return (definite_imports, protected_imports)

def _module_names(imports):
  """Returns a list of module names involved in a list of import names.

  e.g. 'dials.algorithms' will return 'dials'. Any name that isn't a module
  will be missing from the output set."""
  deps = set()
  for potential_dep in imports:
    root_name = potential_dep.split(".")[0]
    if root_name in module_names:
      deps.add(root_name)
  return deps

# Read the command line arguments
options = docopt(__doc__)
dest_dir = options["<module_path>"]

# Search for all modules by looking in the provided directory and matching to known module names
mod_paths = {x: os.path.join(dest_dir, x) for x in os.listdir(dest_dir) if os.path.isdir(os.path.join(dest_dir, x)) and x in module_names}
mod_paths.update({x: os.path.join(dest_dir, "cctbx_project", x) for x in os.listdir(os.path.join(dest_dir, "cctbx_project")) if os.path.isdir(os.path.join(dest_dir, "cctbx_project", x)) and x in module_names})

mod_deps = {"_optional":{}}
# mod_deps_optional = {}

# Read every module that we found to build the map
for module, path in sorted(mod_paths.items()):
  print("Scanning {} for dependencies".format(module), file=sys.stderr)
  imports, optional_imports = ImportVisitor.visit_path(path)

  deps = _module_names(imports) - {module}
  deps_optional = _module_names(optional_imports) - {module}
  # All we care about with optional is those which are not required anyway
  deps_optional -= deps

  # Don't give entries for modules without any python dependencies
  if deps:
    mod_deps[module] = sorted(deps)
  if deps_optional:
    mod_deps["_optional"][module] = sorted(deps_optional)

if options["-o"]:
  with open(options["-o"], "wt") as f:
    yaml.dump(mod_deps, stream=f)
else:
  print(yaml.dump(mod_deps))

