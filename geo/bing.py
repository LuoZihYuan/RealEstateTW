""" Manages geo service provided by Bing """

__all__ = ["Bing"]

# Python Standard Libraries
import json
import datetime
# Third Party Libraries
import yaml
import requests
# Dependent Modules
from geo.provider import Provider, ProviderOutOfAPIKeys, ProviderServerError
from geo.provider import AddressError, CultureError

class Bing(Provider):
    """
        This class inherits from geo.provider.Provider, which gives methods
        of Bing the same paramenters as other geo service providers.
    """
    def __init__(self):
        super(Bing, self).__init__(__file__)

        # shortcut for lengthy dictionary access
        self.config_geocode = self.config["service"]["geocode"]
        self.config_reverse_geocode = self.config["service"]["reverse_geocode"]

        # preparation for geocode method
        self.geocode_keys = []
        for api_key in self.config_geocode["api_keys"]:
            if api_key["key"] and not api_key["expired"]:
                self.geocode_keys.append(api_key)

        # preparation for reverse geocode method
        self.reverse_geocode_keys = []
        for api_key in self.config_reverse_geocode["api_keys"]:
            if api_key["key"] and not api_key["expired"]:
                self.reverse_geocode_keys.append(api_key)

    @classmethod
    def geocode_available(cls):
        with open(__file__.replace(".py", ".yaml"), "r") as config_in:
            config = yaml.load(config_in)
            for api_key in config["service"]["geocode"]["api_keys"]:
                if not api_key["expired"]:
                    return True
        return False

    def geocode(self, address, **kwargs):
        super(Bing, self).geocode(address, **kwargs)

        # check for parameter errors
        culture = "en-US"
        if "culture" in kwargs:
            culture = kwargs["culture"]
            if culture not in self.config_geocode["constraint"][self.PLACEHOLDER_CULTURE]:
                raise CultureError(self.__class__.__name__, culture)

        # attempt to geocode until no keys are available
        query_path = self.config_geocode["api_path"].replace(self.PLACEHOLDER_CULTURE, culture)
        query_path = query_path.replace(self.PLACEHOLDER_ADDRESS, address)
        while self.geocode_keys:
            full_path = query_path.replace(self.PLACEHOLDER_API_KEY, self.geocode_keys[0]["key"])
            response = json.loads(requests.get(full_path).text)
            if response["statusCode"] != 401 and response["statusCode"] != 403:
                break
            expired_key = self.geocode_keys.pop(0)
            expired_key["expired"] = True
            expired_key["expired_time"] = datetime.datetime.now()
        else:
            self.open_config()
            raise ProviderOutOfAPIKeys(self.__class__.__name__)

        # deal with possible error status code
        if response["statusCode"] == 400:
            raise AddressError(self.__class__.__name__, address)
        elif response["statusCode"] == 500 or response["statusCode"] == 503:
            raise ProviderServerError(self.__class__.__name__)

        # return result of geocode
        if response["resourceSets"][0]["estimatedTotal"] != 0:
            coordinates = response["resourceSets"][0]["resources"][0]["point"]["coordinates"].copy()
            return {"lat": coordinates[0], "lon": coordinates[1]}
        return None

    @classmethod
    def reverse_geocode_available(cls):
        with open(__file__.replace(".py", ".yaml"), "r") as config_in:
            config = yaml.load(config_in)
            for api_key in config["service"]["reverse_geocode"]["api_keys"]:
                if not api_key["expired"]:
                    return True
        return False

    def reverse_geocode(self, latitude, longitude):
        raise NotImplementedError