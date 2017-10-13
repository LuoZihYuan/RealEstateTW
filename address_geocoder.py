#pylint: disable=C0321
"""
    Geocode addresses in the database
"""

__all__ = ["main"]

# Python Standard Library
import re
import sqlite3
# Third Party Library
import geo
# Dependent Module
import settings

# user specified constants
IMPORTED_FOLDERS = "IMPORTED_FOLDERS"

COUNTY_PRI = ['A', 'B', 'D', 'E', 'F', 'H', 'C', 'G', 'I', 'J', 'K',\
              'M', 'N', 'O', 'P', 'Q', 'T', 'U', 'V', 'W', 'X', 'Z']
SAMPLE_RATE = 5

# main function related CONSTANTS and functions
def average_geocode(rough_address: str) -> dict:
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
    " Main Process "
    con = sqlite3.connect(settings.__main_db__)
    cur = con.cursor()
    for prefix in COUNTY_PRI:
        bitmask = 1 << (ord(prefix) - 65)
        cur.execute("SELECT quarter FROM {0} WHERE (geocode_log & ?) != ?".format(IMPORTED_FOLDERS),
                    (bitmask, bitmask))
        quarters = [result[0] for result in cur.fetchall()]
        print(quarters)
        for quarter in quarters:
            #TODO: geocode address in quarter
            cur.execute('''UPDATE {0} SET geocode_log = (geocode_log | ?)
                           WHERE quarter = ?;'''.format(IMPORTED_FOLDERS),
                        (bitmask, quarter))
            con.commit()

    con.close()

if __name__ == "__main__":
    main()
