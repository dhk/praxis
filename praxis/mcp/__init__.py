"""Host-side surfaces for the design layer: the MCP server and a local viewer.

Deliberately a subpackage rather than modules in `praxis/`. The build
script copies `praxis/*.py` into the browser bundle with a non-recursive
glob, so everything here stays out of Pyodide — where an MCP transport
and an HTTP server have no meaning and the `mcp` dependency would break
a core that is otherwise stdlib-only.
"""
