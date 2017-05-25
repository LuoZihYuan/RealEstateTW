"""
    this module gives geo.provider a convinient way to update configuration file
"""

__all__ = ["Configuration", "ConfigurationDelegate"]

import abc

class Configuration(dict):
    """
        this class extends default dict type with the ability to track changes of content update
    """
    delegate = None

    def __setitem__(self, key, val):
        super(Configuration, self).__setitem__(key, val)

        # call delegate method to inform dict content updated
        if issubclass(self.delegate.__class__, ConfigurationDelegate):
            self.delegate.configuration_did_update(self)

    def __delitem__(self, key):
        super(Configuration, self).__delitem__(key)

        # call delegate method to inform dict content updated
        if issubclass(self.delegate.__class__, ConfigurationDelegate):
            self.delegate.configuration_did_update(self)

class ConfigurationDelegate(object):
    """
        Protocol/Abstract Class that ensures delegate method of Configuration class
        has been implemented.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def configuration_did_update(self, config):
        """ function called when ObserverDict has been updated """
        pass
