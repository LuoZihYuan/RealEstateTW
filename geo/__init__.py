"""
    Integrate open Geo Services that auto-switches according to
    user defined priority.
"""

__version__ = "0.0.1"
__all__ = ["geocode", "reverse_geocode"]

# Python Standard Library
import os
import sys
from shutil import copyfile
# Third Party Library
import yaml
# Dependent Module
from .provider import *
from .google import *
from .bing import *

# Restrict this package using Python3 and above only
if sys.version_info < (3, 0):
    raise ImportError

PRIORITY_NAME = "priority.yaml"

__folder__ = os.path.abspath(os.path.join(__file__, os.pardir))
__priority__ = os.path.join(__folder__, "config/" + PRIORITY_NAME)

# load in user defined priority
try:
    with open(__priority__, "r") as stream:
        PRIORITY = yaml.load(stream)
except:
    DEFAULT_PRIORITY = os.path.join(__folder__, ".config/" + PRIORITY_NAME)
    copyfile(DEFAULT_PRIORITY, __priority__)
    if sys.platform.startswith("darwin"):
        os.system('open "%s"' %(__priority__))
    elif sys.platform.startswith("linux"):
        os.system('xdg-open "%s"' %(__priority__))
    elif sys.platform.startswith("win"):
        os.system('start "%s"' %(__priority__))
    raise

def geocode(address):
    """ Integrate geocode service of each provider """
    raise NotImplementedError

def reverse_geocode(latitude, longitude):
    """ Integrate reverse geocode service of each provider """
    raise NotImplementedError
