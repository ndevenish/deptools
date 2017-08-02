#!/usr/bin/env python3
# coding: utf-8

"""
Reads and collates a collection of GCC-dependency files output after generage_depsfiles.py

Usage: read_dep_files.py [options] [--restrict=<root>]... <compile_commands>

Options:
  --restrict=<root>   Restrict header dependencies to certain source root(s)
  --output=<file>     Name of yaml file to write to. [default: depdata.yaml]
"""

import fnmatch
from collections import namedtuple, defaultdict
from docopt import docopt
import os, sys
import json
import shlex
import yaml

# from .model import Header, SourceFile
from deptools import DepParser

options = docopt(__doc__)

# Load the compile commands file
commands = json.load(open(options["<compile_commands>"]))

parser = DepParser()

# Turn any restriction paths into glob strings
for dirfilter in options["--restrict"]:
  if not dirfilter.endswith("/"):
    dirfilter += "/*"
  else:
    dirfilter += "*"
  parser.filters.add(dirfilter)

# Read everything in the compile_commands.json file
for command in commands:
  directory = command["directory"]
  source_file = command["file"]
  deps_filename = os.path.join(directory, os.path.basename(source_file)+".hdeps")

  source = parser.parse(deps_filename, source_filename=source_file)
  # Work out the object filename
  command = shlex.split(command["command"])
  objindex = command.index("-o")
  source.object = os.path.normpath(os.path.join(directory, command[objindex+1]))

# Build a dictionary for yaml
d = {
  "source_files": [x.asdict() for x in parser.source_files],
  "headers": [x.asdict() for x in parser.filtered_headers]
}
open(options["--output"], "w").write(yaml.dump(d))
