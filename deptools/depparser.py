# coding: utf-8

import fnmatch
from .model import Header, SourceFile

class DepParser(object):
  """Read multiple GCC-style header depth trees and combine results."""
  def __init__(self, filters=set()):
    self.headers = {}
    self.source_files = []
    self.filters = set(filters)

  def _get_header(self, filename):
    header = self.headers.get(filename)
    if not header:
      header = Header(filename)
      self.headers[filename] = header
    return header

  def _header_allowed(self, filename):
    if filename is None:
      # Means unknown. only safe to allow
      return True
    # if "dials" in filename:
    #   import pdb
    #   pdb.set_trace()
    return all(fnmatch.fnmatch(filename, pattern) for pattern in self.filters)

  @property
  def filtered_headers(self):
    return [x for x in self.headers.values() if self._header_allowed(x.name)]

  def parse(self, filename, source_filename=None):
    lines = [x for x in open(filename).readlines() if x.startswith(".")]

    headers = {}

    source_file = SourceFile(source_filename)
    current_owner = [source_file]
    current_depth = 1

    for line in lines:
      # Extract depth, filename information from this line
      dots, filename = [x.strip() for x in line.split()]
      depth = len(dots)

      # Create the Header node if it doesn't exist
      header = self._get_header(filename)

      # Move down the queue if we need to
      assert depth <= current_depth, "No depth jumps"
      if depth < current_depth:
        current_owner = current_owner[:depth-current_depth]
        current_depth = depth
      
      # Add this header to the previous owner -only if it is not a filtered header.
      # Otherwise, it will exist in the global list but not be connected
      if self._header_allowed(filename) == self._header_allowed(current_owner[-1].name):
        current_owner[-1].add(header)

      # Push this header up the stack
      current_owner.append(header)
      current_depth += 1

    assert len(current_owner) >= 1, "Should never pop last list item"
    self.source_files.append(source_file)
    return source_file
