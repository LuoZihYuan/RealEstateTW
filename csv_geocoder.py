# -*- coding: UTF-8 -*-
#pylint: disable=C0321
"""
    Geocode the addresses in CSV file
"""

__all__ = ["main"]

# Python Standard Library
import os
import re
import csv
import sys
import time
from shutil import copyfile
from enum import Enum, unique
# Third Party Library
import geo
import yaml
# Dependent Module
import settings

# user specified constants
DEAL_PRI = ['A', 'B', 'C'] # (Required)
COUNTY_PRI = ['A', 'B', 'D', 'E', 'F', 'H', 'C', 'G', 'I', 'J', 'K',\
              'M', 'N', 'O', 'P', 'Q', 'T', 'U', 'V', 'W', 'X', 'Z'] # (Optional)
SAMPLE_RATE = 5

# shared CONSTANTS and functions for module
HISTORY_FILE = os.path.join(settings.__config__, "geocode_history.yaml")
BLANK_HISTORY = os.path.join(settings.__hidden__, "geocode_history.yaml")
TEMPORARY_FILE = os.path.join(settings.__resources__, ".temp.CSV")

@unique
class Deal(Enum):
    """ Enum for transaction type """
    sold = 'A'
    presold = 'B'
    rent = 'C'
    def __str__(self):
        return self.value
def file_category(filename: str) -> str:
    """ Classify CSV file by file name """
    code = os.path.splitext(filename)[0][-1]
    return Deal(code).name


# history related CONSTANTS and functions
if not os.path.isfile(HISTORY_FILE):
    copyfile(BLANK_HISTORY, HISTORY_FILE)
with open(HISTORY_FILE, "r") as stream:
    HISTORY = yaml.load(stream)
QUEUE = HISTORY["queue"]
DONE = HISTORY["done"]
def write_history():
    """ Manually called when need to write to history file """
    with open(HISTORY_FILE, "w") as dmp_stream:
        yaml.dump_all([HISTORY], dmp_stream, allow_unicode=True)

def autowrite_history(func):
    """ Decorator for function that needs to write to history file """
    def wrapper(*args, **kwargs):
        """ wrapper for decorator target """
        try:
            return func(*args, **kwargs)
        finally:
            write_history()
    return wrapper

@autowrite_history
def update_history():
    """ Add untracked files to history file """
    # XXX: Should update from config
    for folder in os.listdir(settings.__resources__):
        folderpath = os.path.join(settings.__resources__, folder)
        if folder.startswith('.') or not os.path.isdir(folderpath):
            continue
        for csvfile in os.listdir(folderpath):
            if len(csvfile) != 16:
                continue
            subpath = os.path.join(folder, csvfile)
            dealtype = file_category(subpath)
            if HISTORY["active"] == subpath or\
                subpath in DONE[dealtype] or\
                subpath in QUEUE[dealtype]:
                continue
            QUEUE[dealtype].append(subpath)

@autowrite_history
def next_path():
    """ Get next path from history """
    if HISTORY["active"]:
        return os.path.join(settings.__resources__, HISTORY["active"])
    while DEAL_PRI:
        deal = Deal(DEAL_PRI[0]).name
        if not QUEUE[deal]:
            DEAL_PRI.pop(0)
            continue
        while COUNTY_PRI:
            for short_path in QUEUE[deal]:
                if os.path.basename(short_path)[0] == COUNTY_PRI[0]:
                    HISTORY["active"] = short_path
                    QUEUE[deal].remove(short_path)
                    return os.path.join(settings.__resources__, short_path)
            COUNTY_PRI.pop(0)
        HISTORY["active"] = QUEUE[deal].pop(0)
        return os.path.join(settings.__resources__, HISTORY["active"])
    return None

@autowrite_history
def finish_with_path():
    """ Add finished path into 'done' category of history """
    finished_path = HISTORY["active"]
    HISTORY["active"] = ""
    DONE[file_category(finished_path)].append(finished_path)

def csv_len(filepath: str) -> int:
    """ Count total rows of csv content """
    csv_total = 0
    with open(filepath, "r", encoding='big5', errors='ignore') as filestream:
        for index, _ in enumerate(filestream):
            csv_total = index
    return csv_total

# main function related CONSTANTS and functions
ADDR_COL = "土地區段位置或建物區門牌"
LAT_COL = u"緯度"
LON_COL = u"經度"
def average_geocode(rough_address):
    """ Gets the average GPS coordinates of the rough address interval """
    matches = re.findall(r"\d+~\d+", rough_address)
    if not matches:
        return {"lat": None, "lon": None}
    bound = [int(i) for i in matches[0].split('~')]
    interval = int((bound[1] - bound[0] + 1) / SAMPLE_RATE)
    samples = [i for i in range(bound[0], bound[1] + 1, interval)]
    lat_results = []
    lon_results = []
    for sample in samples:
        query_address = rough_address.replace(matches[0], str(sample))
        gps_coordinates = geo.geocode(query_address, culture='zh-TW')["GPS"]
        if gps_coordinates["lat"] and gps_coordinates["lon"]:
            lat_results.append(gps_coordinates["lat"])
            lon_results.append(gps_coordinates["lon"])
    if lat_results and lon_results:
        lat_avg = sum(lat_results) / len(lat_results)
        lon_avg = sum(lon_results) / len(lon_results)
        return {"lat": lat_avg, "lon": lon_avg}
    raise geo.AddressError(geo.__name__, rough_address)

def main():
    """ Main Process """
    while True:
        print("Checking for untracked files...")
        update_history()

        print("Start geocoding...")
        fullpath = next_path()
        while fullpath:
            total_rows = csv_len(fullpath)
            progress_bar = settings.ProgressBar(total_rows, interval=40, decimals=2,
                                                prefix=HISTORY["active"]+":", suffix='Complete')
            # open file
            csvinput = open(fullpath, "r", encoding='big5', errors='ignore')
            open(TEMPORARY_FILE, "a").close()
            csvoutput = open(TEMPORARY_FILE, "r+", encoding='big5', errors='ignore')

            # parse file using csv
            reader = csv.DictReader(csvinput)
            fieldnames = reader.fieldnames + [LAT_COL, LON_COL]
            skip = csv.DictReader(csvoutput)
            writer = csv.DictWriter(csvoutput, fieldnames)

            # skip handled rows
            if not skip.fieldnames:
                writer.writeheader()
            cached_address = ""
            cached_lat = None
            cached_lon = None
            for row in skip:
                cached_address = row[ADDR_COL]
                cached_lat = row[LAT_COL]
                cached_lon = row[LON_COL]
                next(reader)
                progress_bar.add()

            # write gps result to csv file
            for row in reader:
                target_address = row[ADDR_COL]
                if "地號" in target_address:
                    row[LAT_COL] = None
                    row[LON_COL] = None
                elif target_address == cached_address:
                    row[LAT_COL] = cached_lat
                    row[LON_COL] = cached_lon
                else:
                    cached_exceptions = []
                    while True:
                        try:
                            result_gps = average_geocode(target_address)
                            if cached_exceptions:
                                print("Fixed: ", end='')
                                for excpt in cached_exceptions:
                                    print(excpt, end='')
                                print("")
                                progress_bar.start()
                            row[LAT_COL] = result_gps["lat"]
                            row[LON_COL] = result_gps["lon"]
                            break
                        except geo.AddressError as address_exception:
                            print(address_exception, file=sys.stderr)
                            cached_exceptions.append(address_exception.__class__.__name__)
                            row[LAT_COL] = None
                            row[LON_COL] = None
                            break
                        except Exception as general_exception:
                            if general_exception.__class__.__name__ not in cached_exceptions:
                                print(general_exception, file=sys.stderr)
                                cached_exceptions.append(general_exception.__class__.__name__)
                            time.sleep(10)
                    cached_address = target_address
                    cached_lat = row[LAT_COL]
                    cached_lon = row[LON_COL]
                writer.writerow(row)
                progress_bar.add()
            # close file
            csvinput.close()
            csvoutput.close()
            copyfile(TEMPORARY_FILE, fullpath)
            os.remove(TEMPORARY_FILE)
            finish_with_path()
            fullpath = next_path()
        time.sleep(60)

if __name__ == "__main__":
    main()
