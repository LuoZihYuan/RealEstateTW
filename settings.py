#pylint: disable=C0321,R0902,R0903
""" Shared constants and functions accross modules """

import os

__all__ = ["__config__", "__hidden__", "__resources__", "print_progress_bar", "ProgressBar"]

__config__ = os.path.abspath(os.path.join(__file__, os.pardir, "config"))
__hidden__ = os.path.abspath(os.path.join(__file__, os.pardir, ".RealEstate"))
__resources__ = os.path.abspath(os.path.join(__file__, os.pardir, "resources"))

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
