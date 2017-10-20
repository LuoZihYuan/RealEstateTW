"""
    Shared constants and functions accross the "geo" package
"""

__all__ = ["__config__", "__default__", "open_file"]

import os
import sys

__config__ = os.path.abspath(os.path.join(__file__, os.pardir, "config"))
__default__ = os.path.abspath(os.path.join(__file__, os.pardir, ".geo"))

def open_file(path: str):
    """
        open path using default application regardless of OS difference
    """
    if sys.platform.startswith("darwin"):
        os.system('open "%s"' %(path))
    elif sys.platform.startswith("linux"):
        os.system('xdg-open "%s"' %(path))
    elif sys.platform.startswith("win"):
        os.system('start "%s"' %(path))
