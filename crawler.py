import os
import re
import sys
import requests
from io import BytesIO
from zipfile import ZipFile
from bs4 import BeautifulSoup
from multiprocessing import Pool, Lock

RESOURCES_PATH = "./resources/"

class FileError(Exception):
	"""Missing Requested File"""
	def __init__(self, message, address):
		super(FileError, self).__init__(message)
		self.address = address

def formattedSize(sizeInBytes):
	units = ["byte", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"]
	for unit in units[:-1]:
		if abs(sizeInBytes) < 1024.0:
			return "%3.1f %s" %(sizeInBytes, unit)
		sizeInBytes /= 1024.0
	return "%.1f %s" %(sizeInBytes, units[-1])

def preDownload(l):
	global lock
	lock = l

def downloader(season):
	BASE_URL = "http://plvr.land.moi.gov.tw/DownloadHistory?type=season&fileName="
	url = BASE_URL + season
	httpHeader = requests.head(url).headers
	if "Content-Disposition" in httpHeader:
		fileName = re.search('attachment;filename="(.*)"', httpHeader["Content-Disposition"]).group(1)
	else:
		raise FileError("Missing Open Data", url)
	if "Content-Length" in httpHeader:
		fileSize = int(httpHeader["Content-Length"])
	# locks stdout
	lock.acquire()
	print("Address: " + url)
	print("FileName: '" +  fileName + "'" if fileName else "FileName: Unknown")
	print("Size: " + formattedSize(fileSize) if fileSize else "Size: Unknown")
	lock.release()
	folderName = os.path.splitext(fileName)[0]
	if not os.path.exists(RESOURCES_PATH + folderName):
		os.makedirs(RESOURCES_PATH + folderName)
	file = requests.get(url)
	zippedFile = ZipFile(BytesIO(file.content))
	for dataName in zippedFile.namelist():
		if os.path.splitext(dataName)[1].lower() == '.csv':
			zippedFile.extract(dataName, RESOURCES_PATH + folderName)

if not os.path.exists(RESOURCES_PATH):
	os.makedirs(RESOURCES_PATH)
# TODO: Haven't yet check for local files
seasons = []
print("Checking for updates...")
historyPage = requests.get("http://plvr.land.moi.gov.tw/DownloadHistory_ajax_list")
soup = BeautifulSoup(historyPage.text, "html.parser")
for seasonHTML in soup.select("select#historySeason_id > option"):
	seasons.append(str(seasonHTML.get('value')))
fileCount = len(seasons)
print("Missing %d files\n" %(fileCount))

threads = 1
if fileCount > 1:
	if sys.version_info.major == 2:
		threads = int(raw_input("Download threads: "))
	elif sys.version_info.major == 3:
		threads = int(input("Download threads: "))
	threads = min(threads, fileCount)
print("Downloading...")
lock = Lock()
pool = Pool(processes = 10, initializer=preDownload, initargs=(lock,))
pool.map(downloader, seasons)
pool.close()