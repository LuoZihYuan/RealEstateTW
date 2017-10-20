#pylint: disable=C0321,R0902,R0903
""" Shared constants and functions accross modules """
import os
import sys
from enum import Enum, unique

# global version check
if sys.version_info < (3, 0):
    raise ImportError("Python3 REQUIRED!!")

__all__ = ["__config__", "__hidden__", "__resources__", "print_progress_bar", "ProgressBar"]

__config__ = os.path.abspath(os.path.join(__file__, os.pardir, "config"))
__hidden__ = os.path.abspath(os.path.join(__file__, os.pardir, ".RealEstate"))
__resources__ = os.path.abspath(os.path.join(__file__, os.pardir, "resources"))
__main_db__ = os.path.abspath(os.path.join(__resources__, "main.db"))

GEO_SAMPLES = 5

@unique
class Deal(Enum):
    """ Enum for transaction type """
    sold = 'A'
    presold = 'B'
    rent = 'C'
    def __str__(self):
        return self.value

@unique
class CountyAlpha(Enum):
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
    Taipei_City = '臺北市'; Taichung_City = '臺中市'; Keelung_City = '基隆市'
    Tainan_City = '臺南市'; Kaohsiung_City = '高雄市'; New_Taipei_City = '新北市'
    Yilan_County = '宜蘭縣'; Taoyuan_City = '桃園市'; Chiayi_City = '嘉義市'
    Hsinchu_County = '新竹縣'; Miaoli_County = '苗栗縣'; Nantou_County = '南投縣'
    Changhua_County = '彰化縣'; Hsinchu_City = '新竹市'; Yunlin_County = '雲林縣'
    Chiayi_County = '嘉義縣'; Pingtung_County = '屏東縣'; Hualien_County = '花蓮縣'
    Taitung_County = '臺東縣'; Kinmen_County = '金門縣'; Penghu_County = '澎湖縣'
    Lienchiang_County = '連江縣'

def alpha2cht(alphabet: str) -> str:
    cnty_en = CountyAlpha(alphabet).name
    cnty_cht = CountyCht[cnty_en].value
    return cnty_cht

def cht2alpha(chinese: str) -> str:
    cnty_cht = CountyCht(chinese).name
    cnty_en = CountyAlpha[cnty_cht].value
    return cnty_en

def format_bytes(byte: int) -> str:
    """ Format byte into different magnitude strings """
    units = ["byte", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"]
    for unit in units[:-1]:
        if abs(byte) < 1024.0:
            return "%3.1f %s" %(byte, unit)
        byte /= 1024.0
    return "%.1f %s" %(byte, units[-1])

def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1,
                       length=50, fill='█', overtype=True):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar_graph = fill * filled_length + '-' * (length - filled_length)
    if overtype and iteration:
        print("\033[F", end='')
    print("%s |%s| %s%% %s" %(prefix, bar_graph, percent, suffix))

class ProgressBar(object):
    """ call print progress bar only when interval is reached """
    def __init__(self, total, interval=1, prefix='', suffix='',
                 decimals=1, length=50, fill='█', overtype=True):
        self.total = total; self.prefix = prefix; self.suffix = suffix
        self.decimals = decimals; self.length = length; self.fill = fill
        self.overtype = overtype; self.interval = interval
        self._progress = 0
        self.print_bar()
    def print_bar(self):
        """ convenient call for constant print requests """
        print_progress_bar(self._progress, self.total, self.prefix, self.suffix,
                           self.decimals, self.length, self.fill, self.overtype)
    def start(self):
        """ start printing progress bar at recent line """
        print_progress_bar(0, self.total, self.prefix, self.suffix,
                           self.decimals, self.length, self.fill, self.overtype)
        self.print_bar()
    @property
    def progress(self):
        """ Getter of progress """
        return self._progress
    @progress.setter
    def progress(self, value):
        self._progress = value
        self.start()
    def add(self):
        """ increase progress by one """
        self._progress += 1
        if not self._progress % self.interval:
            self.print_bar()
