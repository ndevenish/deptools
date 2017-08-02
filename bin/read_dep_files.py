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

def dict_diff(first, second):
    diff = {}
    for key in first.keys():
        if (not key in second):
            diff[key] = (first[key], "KEYNOTFOUND")
        elif (first[key] != second[key]):
            diff[key] = (first[key], second[key])
    for key in second.keys():
        if (not key in first):
            diff[key] = ("KEYNOTFOUND", second[key])
    return diff

ddata = parser.asdict()
# Verify that we get the same dictionary by reloading this
assert ddata == DepParser.fromdict(ddata).asdict()

open(options["--output"], "w").write(yaml.dump(ddata))
