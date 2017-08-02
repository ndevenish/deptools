Deptools
--------

A simple set of scripts and tools to work with a clang-style 
`compile_commands.json`, re-run the compiler to extract header tree
information, and make decisions based on that information.

Simple Usage
============

To generate *.hdep files alongside the working directories listed in
`compile_commands.json`:

    generate_depfiles.py some/path/to/compile_commands.json

This will read the database, and re-run the compiler for every file with the
options `-H` (generate header information) and `-E` (preprocessor only). Then,
process these files with:

    read_dep_files.py some/path/to/compile_commands.json

And a file `depdata.yaml` will be created in the current directory. See the 
command `--help` for more options including restricting to header subsets.

API Usage
=========

To process a dumped file (in yaml or any other format) load it into a 
dictionary and pass it to `DepParser.from_dict`:

    # Given an instance of DepParser, parser
    dict_data = parser.asdict()

    from deptools import DepParser
    newParser = DepParser.fromdict(dict_data)

By default, the `read_dep_files.py` tool writes a yaml-converted version
of the dictionary.

The class `deptools.SourceFile` represents files passed directly to the compiler;
they have the properties `.name` and `.object` for the source file and output
object file names, and a collection of `.includes`, an entry for each header file.

The class `deptools.Header` represents any file that is included by another file.
It has a `.name` property, an `.includes` collection (of other header files that it
depends on) and an `.included` collection mapping back to files (headers or source)
that include it.

After loading a `deptools.DepParser` file, you can use the attribute `.source_files`
to access a collection of `SourceFile` objects, and the attribute `.headers` to get
a flat list of **all** header files that are tracked with the object. During
initial processing, it is possible to add a set of filters (`.filters` attribute)
and this reduced header set can be accessed through the `.filtered_headers`
attribute, but note that changing the filters will not remove items from the
`SourceFile` data tree.

