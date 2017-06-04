# -*- coding: UTF-8 -*-
#pylint: disable=C0321
"""
    Geocode the addresses in CSV file
"""

# Python Standard Library
import os
import re
import time
from shutil import copyfile
from enum import Enum, unique
# Third Party Library
import geo
import yaml
import unicodecsv as csv
# Dependent Module
from settings import *


# shared CONSTANTS and functions for module
HISTORY_FILE = os.path.join(__config__, "geocode_history.yaml")
BLANK_HISTORY = os.path.join(__hidden__, "geocode_history.yaml")
TEMPORARY_FILE = os.path.join(__resources__, ".temp.CSV")
DEAL_PRI = ['A', 'B', 'C'] # (Required)
COUNTY_PRI = ['A', 'B', 'D', 'E', 'F', 'H', 'C', 'G', 'I', 'J', 'K',\
              'M', 'N', 'O', 'P', 'Q', 'T', 'U', 'V', 'W', 'X', 'Z'] # (Optional)
SAMPLE_RATE = 5
ADDR_COL = "土地區段位置或建物區門牌"
LAT_COL = "緯度"
LON_COL = "經度"

@unique
class Deal(Enum):
    """ Enum for transaction type """
    sold = 'A'
    presold = 'B'
    rent = 'C'
    def __str__(self):
        return self.value
def file_category(filename):
    """ Classify CSV file by file name """
    code = os.path.splitext(filename)[0][-1]
    return Deal(code).name

@unique
class CountyEng(Enum):
    """ Enum for taiwan counties in english """
    Taipei_City = 'A'; Taichung_City = 'B'; Keelung_City = 'C'
    Tainan_City = 'D'; Kaohsiung_City = 'E'; New_Taipei_City = 'F'
    Yilan_County = 'G'; Taoyuan_City = 'H'; Chiayi_City = 'I'
    Hsinchu_County = 'J'; Miaoli_County = 'K'; Nantou_County = 'M'
    Changhua_County = 'N'; Hsinchu_City = 'O'; Yunlin_County = 'P'
    Chiayi_County = 'Q'; Pingtung_County = 'T'; Hualien_County = 'U'
    Taitung_County = 'V'; Kinmen_County = 'W'; Penghu_County = 'X'
    Lienchiang_County = 'Z'
@unique
class CountyCht(Enum):
    """ Enum for taiwan counties in traditional chinese """
    臺北市 = 'A'; 臺中市 = 'B'; 基隆市 = 'C'
    臺南市 = 'D'; 高雄市 = 'E'; 新北市 = 'F'
    宜蘭縣 = 'G'; 桃園市 = 'H'; 嘉義市 = 'I'
    新竹縣 = 'J'; 苗栗縣 = 'K'; 南投縣 = 'M'
    彰化縣 = 'N'; 新竹市 = 'O'; 雲林縣 = 'P'
    嘉義縣 = 'Q'; 屏東縣 = 'T'; 花蓮縣 = 'U'
    臺東縣 = 'V'; 金門縣 = 'W'; 澎湖縣 = 'X'
    連江縣 = 'Z'


# load geocode history
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
    for folder in os.listdir(__resources__):
        folderpath = os.path.join(__resources__, folder)
        if folder.startswith('.') or not os.path.isdir(folderpath):
            continue
        for csvfile in os.listdir(folderpath):
            if len(csvfile) != 16:
                continue
            subpath = os.path.join(folder, csvfile)
            dealtype = file_category(subpath)
            if HISTORY["active"] == subpath or\
                subpath in DONE or subpath in QUEUE:
                continue
            QUEUE[dealtype].append(subpath)

@autowrite_history
def next_path():
    """ Get next path from history """
    if HISTORY["active"]:
        return os.path.join(__resources__, HISTORY["active"])
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
                    return os.path.join(__resources__, short_path)
            COUNTY_PRI.pop(0)
        HISTORY["active"] = QUEUE[deal].pop(0)
        return os.path.join(__resources__, HISTORY["active"])
    return None

@autowrite_history
def finish_with_path():
    finished_path = HISTORY["active"].copy()
    HISTORY["active"] = ""
    DONE[file_category(finished_path)].append(finished_path)


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
    return {"lat": None, "lon": None}

def main():
    while True:
        update_history()
        fullpath = next_path()
        while fullpath:
            # open file
            csvinput = open(fullpath, "r")
            open(TEMPORARY_FILE, "a").close()
            csvoutput = open(TEMPORARY_FILE, "r+")

            # parse file using csv
            READER = csv.DictReader(csvinput, encoding="big5", errors="ignore")
            FIELDNAMES = READER.fieldnames + [LATITUDE_FIELD, LONGITUDE_FIELD]
            SKIP = csv.DictReader(csvoutput, encoding="big5", errors="ignore")
            WRITER = csv.DictWriter(csvoutput, FIELDNAMES, encoding="big5", errors="ignore")

            # skip handled rows
            if not SKIP.fieldnames:
                WRITER.writeheader()
            cached_address = ""
            cached_lat = None
            cached_lon = None
            for row in SKIP:
                cached_address = row[ADDR_COL]
                cached_lat = row[LAT_COL]
                cached_lon = row[LON_COL]
                next(READER)

            # write gps result to csv file
            for row in READER:
                target_address = row[ADDR_COL]
                if "地號" in target_address:
                    row[LAT_COL] = None
                    row[LON_COL] = None
                elif target_address == cached_address:
                    row[LAT_COL] = cached_lat
                    row[LON_COL] = cached_lon
                else:
                    while True:
                        try:
                            result_gps = average_geocode(target_address)
                            row[LAT_COL] = result_gps["lat"]
                            row[LON_COL] = result_gps["lon"]
                            break
                        except geo.AddressError as e:
                            print(e)
                            row[LAT_COL] = None
                            row[LON_COL] = None
                            break
                        except geo.TryAgainLater:
                            time.sleep(10)
                    cached_address = target_address
                    cached_lat = result_gps["lat"]
                    cached_lon = result_gps["lon"]
                WRITER.writerow(row)
            # close file
            csvinput.close()
            csvoutput.close()
            copyfile(TEMPORARY_FILE, fullpath)
            os.remove(TEMPORARY_FILE)
            finish_with_path()
            fullpath = next_path()
        else:
            time.sleep(60)

if __name__ == "__main__":
    main()
