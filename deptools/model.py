
class CPPFile(object):
  """Abstract node for (headers, sources)"""
  def __init__(self, name=None):
    self.name = name
    self.includes = set()

  def add(self, header):
    self.includes.add(header)

class SourceFile(CPPFile):
  """Represents a CPP, cxx file, that includes headers and has an output"""
  def __init__(self, name=None, object=None):
    super(SourceFile, self).__init__(name)
    self.object = None

  def add(self, header):
    super(SourceFile, self).add(header)
    header.included.add(self)

  def __repr__(self):
    if self.object:
      return "SourceFile('{}', object='{}')".format(self.name, self.object)
    else:
      return "SourceFile('{}')".format(self.name)

  def asdict(self):
    d = {
      "name": self.name,
    }
    if self.object:
      d["object"] = self.object
    if self.includes:
      d["includes"] = list(sorted([x.name for x in self.includes]))
    return d

class Header(CPPFile):
  """Represents a header file, that can be included itself"""
  def __init__(self, name):
    super(Header, self).__init__(name)
    # Files this is included from
    self.included = set()

  def add(self, header):
    super(Header, self).add(header)
    header.included.add(self)

  def __repr__(self):
    return "Header('{}')".format(self.name)

  def asdict(self):
    d = {"name": self.name}
    if self.includes:
      d["includes"] = list(sorted([x.name for x in self.includes]))
    return d


