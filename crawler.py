
""" This module crawls csv files from the Actual Price Registration Platform """

import os
import re
import sys
from io import BytesIO
from multiprocessing import Lock, Pool
from zipfile import ZipFile

import requests
from bs4 import BeautifulSoup

RESOURCES_PATH = "./resources/"
SHARED_LOCK = None

class FileError(Exception):
    """Missing Requested File"""
    def __init__(self, message, address):
        super(FileError, self).__init__(message)
        self.address = address

def formatted_size(size_in_bytes):
    """ Format byte into different magnitude strings """
    units = ["byte", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"]
    for unit in units[:-1]:
        if abs(size_in_bytes) < 1024.0:
            return "%3.1f %s" %(size_in_bytes, unit)
        size_in_bytes /= 1024.0
    return "%.1f %s" %(size_in_bytes, units[-1])

def pre_download(lock):
    """ Setup SHARED_LOCK before process pool starts working """
    global SHARED_LOCK
    SHARED_LOCK = lock

def downloader(season):
    """ Download files using multiprocessing """
    base_url = "http://plvr.land.moi.gov.tw/DownloadHistory?type=season&fileName="
    url = base_url + season
    http_header = requests.head(url).headers
    if "Content-Disposition" in http_header:
        file_name = re.search('attachment;filename="(.*)"', \
		                      http_header["Content-Disposition"]).group(1)
    else:
        raise FileError("Missing Open Data", url)
    if "Content-Length" in http_header:
        file_size = int(http_header["Content-Length"])
    # locks stdout
    SHARED_LOCK.acquire()
    print "Address: " + url
    print "FileName: '" +  file_name + "'" if file_name else "FileName: Unknown"
    print "Size: " + formatted_size(file_size) if file_size else "Size: Unknown"
    SHARED_LOCK.release()
    folder_name = os.path.splitext(file_name)[0]
    if not os.path.exists(RESOURCES_PATH + folder_name):
        os.makedirs(RESOURCES_PATH + folder_name)
    downloaded_file = requests.get(url)
    zipped_file = ZipFile(BytesIO(downloaded_file.content))
    for data_name in zipped_file.namelist():
        if os.path.splitext(data_name)[1].lower() == '.csv':
            zipped_file.extract(data_name, RESOURCES_PATH + folder_name)

if not os.path.exists(RESOURCES_PATH):
    os.makedirs(RESOURCES_PATH)
# TODO: Haven't yet check for local files
SEASONS = []
print "Checking for updates..."
HISTORY_PAGE = requests.get("http://plvr.land.moi.gov.tw/DownloadHistory_ajax_list")
SOUP = BeautifulSoup(HISTORY_PAGE.text, "html.parser")
for seasonHTML in SOUP.select("select#historySeason_id > option"):
    SEASONS.append(str(seasonHTML.get('value')))
FILE_COUNT = len(SEASONS)
print "Missing %d files\n" %(FILE_COUNT)

TOTAL_THREADS = 1
if FILE_COUNT > 1:
    if sys.version_info.major == 2:
        TOTAL_THREADS = int(raw_input("Download threads: "))
    elif sys.version_info.major == 3:
        TOTAL_THREADS = int(input("Download threads: "))
    TOTAL_THREADS = min(TOTAL_THREADS, FILE_COUNT)
print "Downloading..."
LOCK = Lock()
POOL = Pool(processes=10, initializer=pre_download, initargs=(LOCK,))
POOL.map(downloader, SEASONS)
POOL.close()
print "Finish"
