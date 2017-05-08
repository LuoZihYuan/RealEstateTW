
# -*- coding: UTF-8 -*-
""" Geocode address into GPS coordinates """

import os
import re
import yaml
import shutil
import unicodecsv as csv
from geocoder import Geocoder

RESOURCES_PATH = "resources/"
GEOCODE_HISTORY = "geocode_history.yaml"

try:
    YAMLSTREAM = open(GEOCODE_HISTORY, "r+")
except IOError:
    print "Unable to access critical file/directory"
HISTORY = yaml.load(YAMLSTREAM)
def update_yaml():
    """ Update HISTORY back to yaml """
    YAMLSTREAM.seek(0)
    YAMLSTREAM.truncate(0)
    yaml.dump_all([HISTORY], YAMLSTREAM, allow_unicode=True)

CATEGORY = {
    "A": "sold",
    "B": "presold",
    "C": "rent"
}
def categorize(file_name):
    """ Classify CSV file by file name. """
    code = os.path.splitext(file_name)[0][-1]
    return CATEGORY[code]

def get_next_path():
    """ Get next path from history """
    path = ""
    CATEG_PR = ["A", "B", "C"]
    # CITY_PR = ["A", "B", "E", "F", "H"]
    if HISTORY["active"]:
        path = HISTORY["active"]
    else:
        for code in CATEG_PR:
            _cat = categorize(code)
            try:
                path = HISTORY["queue"][_cat].pop(0)
                update_yaml()
                break
            except IndexError:
                continue
    return path

print "Checking for newfiles..."
SUBPATHS = []
for folder in os.listdir(RESOURCES_PATH)[1:]:
    if not os.path.isdir(RESOURCES_PATH + folder):
        continue
    for csvfile in os.listdir(RESOURCES_PATH + folder):
        if len(csvfile) == 16:
            subpath = folder + "/" + csvfile
            cat = categorize(subpath)
            if subpath not in HISTORY["done"][cat] and \
               subpath != HISTORY["active"] and \
               subpath not in HISTORY["queue"][cat]:
                HISTORY["queue"][cat].append(subpath)
update_yaml()

print "Initiating Geocoder..."
shared_geocoder = Geocoder()
def center_gps(raw_address):
    """ Gets the representitive GPS coordinates within the interval of raw_address """
    matches = re.findall(r"\d+~\d+", raw_address)
    lat = None
    lon = None
    if matches:
        match = matches[0]
        bound = match.split("~")
        interval = (int(bound[1]) - int(bound[0]) + 1) / 5
        sample = [i for i in range(int(bound[0])+interval/2, int(bound[1]), interval)]
        lattitude_total = 0.0
        longitude_total = 0.0
        for num in sample[:]:
            address = raw_address.replace(match, str(num))
            coordinates = shared_geocoder.geocode(address)
            if coordinates["lat"] and coordinates["lon"]:
                lattitude_total += coordinates["lat"]
                longitude_total += coordinates["lon"]
            else:
                sample.remove(num)
        if sample:
            lat = lattitude_total / len(sample)
            lon = longitude_total / len(sample)
    return {
        "lat": lat,
        "lon": lon
    }

TEMPORARY_FILE = ".temp.CSV"
ADDRESS_FIELD = u"土地區段位置或建物區門牌"
LATITUDE_FIELD = u"緯度"
LONGITUDE_FIELD = u"經度"
BANNED_KEYWORD = u"地號"
GARBLED_LETTER = "&#"

next_path = get_next_path()
while next_path:
    print "Geocoding " + next_path
    with open(RESOURCES_PATH + next_path, "r") as csvinput:
        HISTORY["active"] = next_path
        update_yaml()
        reader = csv.DictReader(csvinput, encoding="big5", errors="ignore")
        fieldnames = reader.fieldnames + [LATITUDE_FIELD, LONGITUDE_FIELD]
        with open(RESOURCES_PATH + TEMPORARY_FILE, "a") as createfile:
            pass
        with open(RESOURCES_PATH + TEMPORARY_FILE, "r+") as csvoutput:
            skip_reader = csv.DictReader(csvoutput, encoding="big5", errors="ignore")
            writer = csv.DictWriter(csvoutput, fieldnames, encoding="big5", errors="ignore")
            previous_address = ""
            previous_gps = {"lat": None, "lon": None}
            if not skip_reader.fieldnames:
                writer.writeheader()
            for row in skip_reader:
                previous_address = row[ADDRESS_FIELD]
                previous_gps["lat"] = row[LATITUDE_FIELD]
                previous_gps["lon"] = row[LONGITUDE_FIELD]
                reader.next()
            for row in reader:
                rough_address = row[ADDRESS_FIELD]
                if BANNED_KEYWORD in rough_address or GARBLED_LETTER in rough_address:
                    pass
                elif previous_address == rough_address:
                    row[LATITUDE_FIELD] = previous_gps["lat"]
                    row[LONGITUDE_FIELD] = previous_gps["lon"]
                elif previous_address != rough_address:
                    result = center_gps(rough_address)
                    row[LATITUDE_FIELD] = result["lat"]
                    row[LONGITUDE_FIELD] = result["lon"]
                    previous_address = rough_address
                    previous_gps["lat"] = result["lat"]
                    previous_gps["lon"] = result["lon"]
                writer.writerow(row)
    shutil.copyfile(RESOURCES_PATH + TEMPORARY_FILE, RESOURCES_PATH + next_path)
    os.remove(RESOURCES_PATH + TEMPORARY_FILE)
    HISTORY["done"][categorize(next_path)].append(next_path)
    HISTORY["active"] = ""
    update_yaml()
    next_path = get_next_path()

YAMLSTREAM.close()
