"""
    This module does basic setup for all Geo Providers.
    Abstractmethod ensures subclass provides functionalities such as geocode, reverse_geocode, etc.
"""

__all__ = ["Provider", "ProviderOutOfAPIKeys", "ProviderServerError", "AddressError",
           "CultureError"]

# Python Standard Libraries
import os
import abc
import sys
# Third Party Libraries
import yaml
# Dependent Modules
from geo.configuration import *

class ProviderOutOfAPIKeys(Exception):
    """ all API Keys of specific provider has expired """
    def __init__(self, provider):
        super(ProviderOutOfAPIKeys, self).__init__()
        self.provider = provider
    def __str__(self):
        return self.provider

class ProviderServerError(Exception):
    """ server of specific provider is currently unavailable """
    def __init__(self, provider):
        super(ProviderServerError, self).__init__()
        self.provider = provider
    def __str__(self):
        return self.provider

class AddressError(Exception):
    """ address provided is invalid """
    def __init__(self, provider, address):
        super(AddressError, self).__init__()
        self.provider = provider
        self.address = address
    def __str__(self):
        return "'%s' can not recognize address '%s'" %(self.provider, self.address)

class CultureError(Exception):
    """ culture code specified is not supported by specific provider """
    def __init__(self, provider, culture):
        super(CultureError, self).__init__()
        self.provider = provider
        self.culture = culture
    def __str__(self):
        return "'%s' does not support culture code '%s'" %(self.provider, self.culture)

class Provider(ConfigurationDelegate):
    """ Base class for all Geo-providers """

    __metaclass__ = abc.ABCMeta

    PLACEHOLDER_API_KEY = "$1"
    PLACEHOLDER_ADDRESS = "$2"
    PLACEHOLDER_CULTURE = "$3"

    def __new__(cls, *args, **kwargs):
        if cls is Provider:
            raise TypeError("Class 'Provider' may not be directly instantiated.")
        return super(Provider, cls).__new__(cls, *args, **kwargs)

    def __init__(self, filepath):
        # load in configuration file for corresponding geo service providers
        self.__config__ = filepath.replace(".py", ".yaml")
        with open(self.__config__, "r") as config_in:
            self.config = Configuration(yaml.load(config_in))
            self.config.delegate = self

        # prompt rough message of geo service providers
        print("Provider: " + self.__class__.__name__)
        print("Website: ", end='')
        try:
            print('"%s"' %(self.config["website"]))
        except KeyError:
            print()
            self.open_config()
            raise

    def open_config(self):
        """ open config file with user's default application for yaml file extension """
        if sys.platform.startswith("darwin"):
            os.system('open "%s"' %(self.__config__))
        elif sys.platform.startswith("linux"):
            os.system('xdg-open "%s"' %(self.__config__))
        elif sys.platform.startswith("win"):
            os.system('start "%s"' %(self.__config__))

    def configuration_did_update(self, config):
        with open(self.__config__, "w") as config_out:
            yaml.dump(dict(config), config_out)

    @abc.abstractclassmethod
    def geocode_available(cls):
        """ Checks if geocode service is potentially available. """
        pass

    @abc.abstractmethod
    def geocode(self, address, **kwargs):
        """
            Get GPS coordinates by geographical address.
            Method specified by each subclass.
        """
        # check if garbled letters exist in address
        banned_symbol = "&#"
        for symbol in banned_symbol:
            if symbol in address:
                raise AddressError(self.__class__.__name__, address)

    @abc.abstractclassmethod
    def reverse_geocode_available(cls):
        """ Checks if reverse geocode service is potentially available. """
        pass

    @abc.abstractmethod
    def reverse_geocode(self, latitude, longitude):
        """
            Get geographical address by GPS coordinates.
            Method specified by each subclass.
         """
        pass
