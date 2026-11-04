"""Tool registration. Add a new tool module here and call its register()."""

from franka_mcp.tools import control, prepare, status, tasks

MODULES = (status, tasks, control, prepare)


def register_all(mcp):
    for module in MODULES:
        module.register(mcp)
