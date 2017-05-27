""" Manages geo service provided by Google """

# Python Standard Library
import json
import datetime
# Third Party Library
import yaml
import requests
# Dependent Module
from geo.provider import Provider, Placeholder, ProviderOutOfAPIKeys, ProviderServerError
from geo.provider import AddressError

class Google(Provider):
    """
        This class inherits from geo.provider.Provider, which gives methods
        of Google the same paramenters as other geo service providers.
    """
    def __init__(self):

        super(Google, self).__init__(__file__)

        # shortcut for lengthy dictionary access
        self.config_geocode = self.config["service"]["geocode"]
        # self.config_reverse_geocode = self.config["service"]["reverse_geocode"]

        # preparation for geocode method
        self.geocode_keys = []
        for api_key in self.config_geocode["api_keys"]:
            if api_key["key"] and not api_key["expired"]:
                self.geocode_keys.append(api_key)

        # preparation for reverse geocode method
        # self.reverse_geocode_keys = []
        # for api_key in self.config_reverse_geocode["api_keys"]:
        #     if api_key["key"] and not api_key["expired"]:
        #         self.reverse_geocode_keys.append(api_key)

    @classmethod
    def geocode_available(cls):
        with open(__file__.replace(".py", ".yaml"), "r") as config_in:
            config = yaml.load(config_in)
            for api_key in config["service"]["geocode"]["api_keys"]:
                if not api_key["expired"]:
                    return True
        return False

    def geocode(self, address, **kwargs):
        super(Google, self).geocode(address, **kwargs)

        # attempt to geocode until no keys are available
        query_path = self.config_geocode["api_path"].replace(str(Placeholder.ADDRESS), address)
        while self.geocode_keys:
            full_path = query_path.replace(str(Placeholder.API_KEY), self.geocode_keys[0]["key"])
            response = json.loads(requests.get(full_path).text)
            status = response["status"]
            if status != "OVER_QUERY_LIMIT" and status != "REQUEST_DENIED":
                break
            expired_key = self.geocode_keys.pop(0)
            expired_key["expired"] = True
            expired_key["expired_time"] = datetime.datetime.now()
        else:
            self.open_config()
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
        return None
