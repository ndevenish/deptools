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
    dict_data = parser.as_dict()

    from deptools import DepParser
    newParser = DepParser.from_dict(dict_data)

By default, the `read_dep_files.py` tool writes a yaml-converted version
of the dictionary.
