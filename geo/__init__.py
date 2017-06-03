"""
    Integrate open Geo Services that auto-switches according to
    user defined priority.
"""

__version__ = "0.0.1"
__all__ = ["geocode"]
# __all__ = ["geocode", "reverse_geocode"]

# Python Standard Library
import os
import sys
from shutil import copyfile
# Third Party Library
import yaml
# Dependent Module
import geo.dependency as dependency
from .settings import *
from .provider import *

# Restrict this package using Python3 and above only
if sys.version_info < (3, 0):
    raise ImportError

class TryAgainLater(Exception):
    """ Retry later might solve the current problem """
    pass

PRIORITY_NAME = "priority.yaml"

__priority__ = os.path.join(__config__, PRIORITY_NAME)

# load in user defined priority
try:
    with open(__priority__, "r") as stream:
        PRIORITY = yaml.load(stream)
except:
    DEFAULT_PRIORITY = os.path.join(__default__ + PRIORITY_NAME)
    copyfile(DEFAULT_PRIORITY, __priority__)
    open_file(__priority__)
    raise

# instantiate providers in dependency
PROVIDERS = {}
for name in dir(dependency):
    if "__" not in name:
        classtype = getattr(dependency, name)
        if issubclass(classtype, Provider):
            PROVIDERS[name] = classtype()

# sort provider instances according to prority
GEOCODE_INSTANCES = []
for pro_name in PRIORITY["geocode"]:
    GEOCODE_INSTANCES.append(PROVIDERS[pro_name])
for key in PROVIDERS:
    if key not in PRIORITY["geocode"]:
        GEOCODE_INSTANCES.append(PROVIDERS[key])

# REVERSE_GEOCODE_INSTANCES = []
# for pro_name in PRIORITY["reverse_geocode"]:
#     REVERSE_GEOCODE_INSTANCES.append(providers[pro_name])
# for key in providers:
#     if key not in PRIORITY["reverse_geocode"]:
#         REVERSE_GEOCODE_INSTANCES.append(providers[key])

def geocode(address, provider=None, **kwargs):
    """ Integrate geocode service of each provider """
    # check if garbled letters exist in address
    banned_symbol = "&#"
    for symbol in banned_symbol:
        if symbol in address:
            raise AddressError(Provider.__class__.__name__, address)

    # doesn't handle exception if provider is specified
    if provider and issubclass(provider, Provider):
        return {"provider": provider.__class__.__name__,
                "GPS": provider.geocode(address, **kwargs)}

    # greedy attempt using different providers
    error_log = []
    for instance in GEOCODE_INSTANCES:
        if instance.geocode_available():
            try:
                return {"provider": instance.__class__.__name__,
                        "GPS": instance.geocode(address, **kwargs)}
            except (ProviderOutOfAPIKeys, ProviderServerError, AddressError, CultureError) as error:
                error_log.append(error)
                continue

    # check if address isn't recognized by any providers
    for error in error_log:
        if not isinstance(error, AddressError):
            break
    else:
        raise AddressError(Provider.__class__.__name__, address)
    raise TryAgainLater

# def reverse_geocode(latitude, longitude):
#     """ Integrate reverse geocode service of each provider """
#     raise NotImplementedError
