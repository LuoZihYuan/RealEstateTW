"""
    This module does basic setup for all Geo Providers.
    Abstractmethod ensures subclass provides functionalities such as geocode, reverse_geocode, etc.
"""

__all__ = ["Provider", "ProviderOutOfAPIKeys", "ProviderServerError",\
           "AddressError", "CultureError"]

# Python Standard Library
import os
import abc
from shutil import copyfile
from enum import Enum, unique
# Third Party Library
import yaml
# Dependent Module
from .settings import *


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


@unique
class Placeholder(Enum):
    """ Gloabal placeholder for api paths """
    API_KEY = 1
    ADDRESS = 2
    CULTURE = 3
    LATITUDE = 4
    LONGITUDE = 5

    def __str__(self):
        return "$%d" %(self.value)


class Provider(object):
    """ Base class for all Geo-providers """

    __metaclass__ = abc.ABCMeta

    def __new__(cls, *args, **kwargs):
        if cls is Provider:
            raise TypeError("Class 'Provider' should not be directly instantiated.")
        return super(Provider, cls).__new__(cls, *args, **kwargs)

    def __init__(self, filepath: str, showPrompt:bool=True):
        # load in configuration file for corresponding geo service providers
        filename = os.path.basename(filepath)
        self.__yaml__ = os.path.join(__config__, filename.replace(".py", ".yaml"))
        try:
            with open(self.__yaml__, "r") as config_in:
                self.config = yaml.load(config_in)
        except:
            blank_config = os.path.join(__default__, filename.replace(".py", ".yaml"))
            copyfile(blank_config, self.__yaml__)
            open_file(self.__yaml__)
            raise

        # prompt rough message of geo service providers if successfully inheritted
        try:
            self.website = self.config["website"]
        except KeyError:
            open_file(self.__yaml__)
            raise
        if showPrompt:
            print("Provider: " + self.__class__.__name__)
            print("Website: " + self.website)

    @abc.abstractclassmethod
    def geocode_available(cls):
        """ Checks if geocode service is potentially available. """
        pass

    @abc.abstractmethod
    def geocode(self, address: str, **kwargs):
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
        raise NotImplementedError

    @abc.abstractmethod
    def reverse_geocode(self, latitude: float, longitude: float):
        """
            Get geographical address by GPS coordinates.
            Method specified by each subclass.
        """
        raise NotImplementedError


def provider_config_update(func):
    """ Decorator for method that possibly changes config and needs to update to file """
    def wrapper(self, *args, **kwargs):
        """ deal with decorator target """
        if not issubclass(self.__class__, Provider):
            raise TypeError("provider_config_update decorator can only be used with\
                             class subclassing 'Provider'")
        try:
            return func(self, *args, **kwargs)
        finally:
            with open(self.__yaml__, "w") as config_out:
                yaml.dump(self.config, config_out)
    return wrapper
