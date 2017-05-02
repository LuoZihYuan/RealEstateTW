""" Integrate all common geocoding APIs """
# XXX: use module instead of class
import os
import json
import shutil
import yaml
import requests

EXAMPLE_PATH = ".RealEstate/"
EXAMPLE_FILE_EXTENSION = ".example"
CONFIG_FILE_NAME = "config.yaml"

class MissingApiKeyException(Exception):
    """ API keys are required for every geocoding service. """
    pass

class Geocoder(object):
    """ The main Geocoder class """
    services = []
    current_service = {}

    def __init__(self):
        try:
            if not os.path.exists(CONFIG_FILE_NAME):
                shutil.copy2(EXAMPLE_PATH + CONFIG_FILE_NAME + EXAMPLE_FILE_EXTENSION, CONFIG_FILE_NAME)
        except IOError:
            print "Unable to access critical file/directory"
        with open(CONFIG_FILE_NAME, "r+") as stream:
            config = yaml.load(stream)
            for service in config["geocoder"]:
                if service["key"]:
                    self.services.append(service)
            if len(self.services) == 0:
                raise MissingApiKeyException
            self.current_service = self.services[0]

    @classmethod
    def __bing_maps(cls, response):
        latitude = None
        longitude = None
        results = response["resourceSets"][0]
        if results["estimatedTotal"] != 0:
            coordinates = results["resources"][0]["point"]["coordinates"]
            latitude = coordinates[0]
            longitude = coordinates[1]
        return {
            "lat": latitude,
            "lon": longitude
        }

    @classmethod
    def __google_maps(cls, response):
        latitude = None
        longitude = None
        if response["status"] != "ZERO_RESULTS":
            location = response["results"][0]["geometry"]["location"]
            latitude = location["lat"]
            longitude = location["lng"]
        return {
            "lat": latitude,
            "lon": longitude
        }

    def geocode(self, address):
        """ Geocodes address into GPS coordinates """
        base_url = self.current_service["path"]
        placeholder = self.current_service["placeholder"]
        path = base_url.replace(placeholder["address"], address)
        for key in self.current_service["key"]:
            path = path.replace(placeholder["key"], key)
        response = json.loads(requests.get(path).text)
        subname = self.current_service["name"].replace(" ", "_").lower()
        validate_method = "_" + self.__class__.__name__ + "__" + subname
        return getattr(Geocoder, validate_method)(response)
