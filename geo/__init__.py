"""
    Integrate open Geo Services that auto-switches according to user defined priority.
"""

__version__ = "0.0.1"
__all__ = ["geocode"]

import os
import sys
import yaml
from .provider import *
from .google import *
from .bing import *

if sys.version_info < (3, 0):
    raise ImportError

__folder__ = os.path.abspath(os.path.join(__file__, os.pardir))
PRIORITY_FILE = os.path.join(__folder__, "priority.yaml")

a = Google()
with open(PRIORITY_FILE, "r") as stream:
    priority = yaml.load(stream)

def geocode(address):
    """  """
    geocode_pri = priority["geocode"]
