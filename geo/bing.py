""" Manages geo service provided by Bing """

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
from .provider import ProviderOutOfAPIKeys, ProviderServerError, AddressError, CultureError

class Bing(Provider):
    """
        This class inherits from geo.provider.Provider, which gives methods
        of Bing the same paramenters as other geo service providers.
    """
    def __init__(self):
        super(Bing, self).__init__(__file__, showPrompt=False)

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
        super(Bing, self).geocode(address, **kwargs)

        # check for parameter errors
        culture = "en-US"
        if "culture" in kwargs:
            culture = kwargs["culture"]
            if culture not in self.config_geocode["constraint"][str(Placeholder.CULTURE)]:
                raise CultureError(self.__class__.__name__, culture)

        # attempt to geocode until no keys are available
        query_path = self.config_geocode["api_path"].replace(str(Placeholder.CULTURE), culture)
        query_path = query_path.replace(str(Placeholder.ADDRESS), address)
        for api_key in self.config_geocode["api_keys"]:
            if api_key["expired"]:
                elapsed_time = datetime.now() - api_key["expired_time"]
                if elapsed_time.days <= 0:
                    continue
            full_path = query_path.replace(str(Placeholder.API_KEY), api_key["key"])
            response = json.loads(requests.get(full_path).text)
            statusCode = response["statusCode"]
            if statusCode != 401 and statusCode != 403:
                api_key["expired"] = False
                api_key["expired_time"] = None
                break
            if not api_key["expired"]:
                api_key["expired"] = True
                api_key["expired_time"] = datetime.now()
        else:
            open_file(self.__yaml__)
            raise ProviderOutOfAPIKeys(self.__class__.__name__)

        # deal with possible error status code
        if statusCode == 400:
            raise AddressError(self.__class__.__name__, address)
        elif statusCode == 500 or statusCode == 503:
            raise ProviderServerError(self.__class__.__name__)

        # return result of geocode
        if response["resourceSets"][0]["estimatedTotal"] != 0:
            coordinates = response["resourceSets"][0]["resources"][0]["point"]["coordinates"].copy()
            return {"lat": coordinates[0], "lon": coordinates[1]}
        return {"lat": None, "lon": None}
