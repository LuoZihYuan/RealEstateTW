""" Manages geo service provided by Google """

# Python Standard Library
import os
import json
from datetime import datetime
# Third Party Library
import yaml
import requests
# Dependent Module
from .settings import *
from .provider import Provider, Placeholder, provider_config_update
from .provider import ProviderOutOfAPIKeys, ProviderServerError, AddressError

class Google(Provider):
    """
        This class inherits from geo.provider.Provider, which gives methods
        of Google the same paramenters as other geo service providers.
    """
    def __init__(self):

        super(Google, self).__init__(__file__, showPrompt=False)

        # shortcut for lengthy dictionary access
        self.config_geocode = self.config["service"]["geocode"]
        # self.config_reverse_geocode = self.config["service"]["reverse_geocode"]

        # preparation for reverse geocode method
        # self.reverse_geocode_keys = []
        # for api_key in self.config_reverse_geocode["api_keys"]:
        #     if api_key["key"] and not api_key["expired"]:
        #         self.reverse_geocode_keys.append(api_key)

    @classmethod
    def geocode_available(cls):
        filename = os.path.basename(__file__)
        path = os.path.join(__config__, filename.replace(".py", ".yaml"))
        with open(path, "r") as stream:
            config = yaml.load(stream)
        for api_key in config["service"]["geocode"]["api_keys"]:
            if not api_key["expired"]:
                return True
            elapsed_time = datetime.now() - api_key["expired_time"]
            if elapsed_time.days > 0:
                return True
        return False

    @provider_config_update
    def geocode(self, address: str, **kwargs):
        super(Google, self).geocode(address, **kwargs)

        # attempt to geocode until no keys are available
        query_path = self.config_geocode["api_path"].replace(str(Placeholder.ADDRESS), address)
        for api_key in self.config_geocode["api_keys"]:
            if api_key["expired"]:
                elapsed_time = datetime.now() - api_key["expired_time"]
                if elapsed_time.days <= 0:
                    continue
            full_path = query_path.replace(str(Placeholder.API_KEY), api_key["key"])
            response = json.loads(requests.get(full_path).text)
            status = response["status"]
            if status != "OVER_QUERY_LIMIT" and status != "REQUEST_DENIED":
                api_key["expired"] = False
                api_key["expired_time"] = None
                break
            if not api_key["expired"]:
                api_key["expired"] = True
                api_key["expired_time"] = datetime.now()
        else:
            open_file(self.__yaml__)
            raise ProviderOutOfAPIKeys(self.__class__.__name__)
            
        # deal with possible error status
        if status == "INVALID_REQUEST":
            raise AddressError(self.__class__.__name__, address)
        elif status == "UNKNOWN_ERROR":
            raise ProviderServerError(self.__class__.__name__)

        # return result of geocode
        if status != "ZERO_RESULTS":
            location = response["results"][0]["geometry"]["location"]
            return {"lat": location["lat"], "lon": location["lng"]}
        return {"lat": None, "lon": None}
