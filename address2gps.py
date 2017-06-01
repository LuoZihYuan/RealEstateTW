# -*- coding: UTF-8 -*-
"""
    Geocode address into GPS coordinates
"""

# Python Standard Library
import os
import re
import shutil
# Third Party Library
import geo
import yaml
import unicodecsv as csv

RESOURCES_PATH = "resources/"
GEOCODE_HISTORY = "geocode_history.yaml"

try:
    YAMLSTREAM = open(GEOCODE_HISTORY, "r+")
except IOError:
    print("Unable to access critical file/directory")
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
    categ_pr = ["A", "B", "C"]
    # CITY_PR = ["A", "B", "E", "F", "H"]
    if HISTORY["active"]:
        path = HISTORY["active"]
    else:
        for code in categ_pr:
            _cat = categorize(code)
            try:
                path = HISTORY["queue"][_cat].pop(0)
                update_yaml()
                break
            except IndexError:
                continue
    return path

print("Checking for newfiles...")
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

print("Initiating Geocoder...")
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
            coordinates = geo.geocode(address)
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

NEXT_PATH = get_next_path()
while NEXT_PATH:
    print("Geocoding " + NEXT_PATH)
    with open(RESOURCES_PATH + NEXT_PATH, "r") as csvinput:
        HISTORY["active"] = NEXT_PATH
        update_yaml()
        READER = csv.DictReader(csvinput, encoding="big5", errors="ignore")
        FIELDNAMES = READER.fieldnames + [LATITUDE_FIELD, LONGITUDE_FIELD]
        with open(RESOURCES_PATH + TEMPORARY_FILE, "a") as createfile:
            pass
        with open(RESOURCES_PATH + TEMPORARY_FILE, "r+") as csvoutput:
            SKIP_READER = csv.DictReader(csvoutput, encoding="big5", errors="ignore")
            WRITER = csv.DictWriter(csvoutput, FIELDNAMES, encoding="big5", errors="ignore")
            PREVIOUS_ADDRESS = ""
            PREVIOUS_GPS = {"lat": None, "lon": None}
            if not SKIP_READER.fieldnames:
                WRITER.writeheader()
            for row in SKIP_READER:
                previous_address = row[ADDRESS_FIELD]
                PREVIOUS_GPS["lat"] = row[LATITUDE_FIELD]
                PREVIOUS_GPS["lon"] = row[LONGITUDE_FIELD]
                READER.next()
            for row in READER:
                rough_address = row[ADDRESS_FIELD]
                if BANNED_KEYWORD in rough_address:
                    pass
                elif previous_address == rough_address:
                    row[LATITUDE_FIELD] = PREVIOUS_GPS["lat"]
                    row[LONGITUDE_FIELD] = PREVIOUS_GPS["lon"]
                elif previous_address != rough_address:
                    result = center_gps(rough_address)
                    row[LATITUDE_FIELD] = result["lat"]
                    row[LONGITUDE_FIELD] = result["lon"]
                    previous_address = rough_address
                    PREVIOUS_GPS["lat"] = result["lat"]
                    PREVIOUS_GPS["lon"] = result["lon"]
                WRITER.writerow(row)
    shutil.copyfile(RESOURCES_PATH + TEMPORARY_FILE, RESOURCES_PATH + NEXT_PATH)
    os.remove(RESOURCES_PATH + TEMPORARY_FILE)
    HISTORY["done"][categorize(NEXT_PATH)].append(NEXT_PATH)
    HISTORY["active"] = ""
    update_yaml()
    NEXT_PATH = get_next_path()

YAMLSTREAM.close()
