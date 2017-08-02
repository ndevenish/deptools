# coding: utf-8

import fnmatch
from .model import Header, SourceFile

class DepParser(object):
  """Read multiple GCC-style header depth trees and combine results."""
  def __init__(self, filters=set()):
    self._headers = {}
    self.source_files = []
    self.filters = set(filters)

  def _get_header(self, filename):
    header = self._headers.get(filename)
    if not header:
      header = Header(filename)
      self._headers[filename] = header
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
  def headers(self):
    return self._headers.items()

  @property
  def filtered_headers(self):
    """Get the subset of known headers that pass the filters"""
    return [x for x in self._headers.values() if self._header_allowed(x.name)]

  def parse(self, filename, source_filename=None):
    "Parse a dependency file and add it to the database graph"
    lines = [x for x in open(filename).readlines() if x.startswith(".")]

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

  def asdict(self):
    d = {
      "source_files": [x.asdict() for x in sorted(self.source_files, key=lambda x: x.name)],
      "headers": [x.asdict() for x in sorted(self.filtered_headers, key=lambda x: x.name)]
    }
    return d

  @classmethod
  def fromdict(cls, d):
    """From a dictionary, reconstruct the source graph"""
    parser = cls()
    for dsource in d["source_files"]:
      source = SourceFile(dsource["name"])
      source.object = dsource.get("object")
      parser.source_files.append(source)

      for filename in dsource.get("includes", []):
        header = parser._get_header(filename)
        source.includes.add(header)
    for dheader in d["headers"]:
      header = parser._get_header(dheader["name"])
      for filename in dheader.get("includes",[]):
        header.add(parser._get_header(filename))
    return parser




