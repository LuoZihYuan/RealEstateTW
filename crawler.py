"""
    This module crawls csv files from the Actual Price Registration Platform
"""

# Standard Python Library
import os
import re
import errno
from io import BytesIO
from zipfile import ZipFile
from multiprocessing.dummy import Lock as ThreadLock
from multiprocessing.dummy import Pool as ThreadPool
# Third Party Library
import requests
import settings
from bs4 import BeautifulSoup

HISTORY_LIST_URL = "http://plvr.land.moi.gov.tw/DownloadHistory_ajax_list"
def update_check():
    """ Check for new seasonal updates """
    seasons = []
    recent_resources = os.listdir(settings.__resources__)
    history_page = requests.get(HISTORY_LIST_URL)
    soup = BeautifulSoup(history_page.text, "html.parser")
    for season_option in soup.select("select#historySeason_id > option"):
        season = season_option.get('value')
        if season not in recent_resources:
            seasons.append(season)
    return seasons

SHARED_LOCK = ThreadLock()
DOWNLOAD_BASE_URL = "http://plvr.land.moi.gov.tw/DownloadHistory?type=season&fileName={}"
def downloader(season: str):
    """ Download files and extract to resources folder """
    url = DOWNLOAD_BASE_URL.format(season)
    http_header = requests.head(url).headers
    if "Content-Disposition" in http_header:
        file_name = re.search('attachment;filename="(.*)"', \
		                      http_header["Content-Disposition"]).group(1)
    else:
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), url)
    if "Content-Length" in http_header:
        file_size = int(http_header["Content-Length"])
    # locks stdout
    SHARED_LOCK.acquire()
    print("Address: " + url)
    print("FileName: '" +  file_name + "'" if file_name else "FileName: Unknown")
    print("Size: " + settings.format_bytes(file_size) if file_size else "Size: Unknown")
    SHARED_LOCK.release()
    # download file
    downloaded_file = requests.get(url)
    # unzip csv file into folder
    zipped_file = ZipFile(BytesIO(downloaded_file.content))
    folder_name = os.path.join(settings.__resources__, season)
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    for data_name in zipped_file.namelist():
        if os.path.splitext(data_name)[1].lower() == '.csv':
            zipped_file.extract(data_name, folder_name)

def main():
    """ Main Function """
    print("Checking for updates...")
    new_files = update_check()
    file_count = len(new_files)
    if file_count:
        print("Missing %d files\n" %(file_count))
        print("Downloading...")
        pool = ThreadPool(file_count)
        pool.map(downloader, new_files)
        pool.close()
    print("\nFinish")

if __name__ == "__main__":
    main()
