#!/usr/bin/env python3
# coding: utf-8

"""
Generate GCC-header dependency files for each entry in a compile_commands.json file.

Usage:
  generate_depfiles.py <compile_commands>

"""

import os, sys
import json
import subprocess
import shlex
import locale

from docopt import docopt

def check_error_output(*args, **kwargs):
  proc = subprocess.run(*args,
      stdout=subprocess.DEVNULL,
      stderr=subprocess.PIPE,
      **kwargs)
  assert not proc.returncode
  return proc.stderr.decode(sys.getfilesystemencoding())

options = docopt(__doc__)

commands = json.load(open(options["<compile_commands>"]))


for command in commands:
  # directory, command, file
  directory = command["directory"]
  source_file = command["file"]
  command = shlex.split(command["command"])
  command.extend(["-H", "-E"])

  output_filename = os.path.join(directory, os.path.basename(source_file)+".hdeps")
  print("Running {}".format(" ".join(command)))
  dep_data = check_error_output(command, cwd=directory)

  print("  Writing {}".format(output_filename))
  with open(output_filename, "w") as output:
    # print(source_file, file=output)
    output.write(dep_data)


