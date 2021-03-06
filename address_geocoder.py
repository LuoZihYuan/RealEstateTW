#pylint: disable=C0321
"""
    Geocode addresses in the database
"""

__all__ = ["main"]

# Python Standard Library
import os
import re
import sys
import time
import sqlite3
# Third Party Library
import geo
# Dependent Module
import settings

IMPORTED_FOLDERS = "IMPORTED_FOLDERS"
COUNTY_PRI = ['A', 'B', 'D', 'E', 'F', 'H', 'C', 'G', 'I', 'J', 'K',\
              'M', 'N', 'O', 'P', 'Q', 'T', 'U', 'V', 'W', 'X', 'Z']

# XXX: add input of sample rate
def selective_geocode(rough_address: str) -> dict:
    """ Gets the average GPS coordinates of the rough address interval """
    lat_results = []; lon_results = []
    found = re.findall(r"\d+~\d+", rough_address)
    if not found:
        raise geo.AddressError(geo.__name__, rough_address)
    bound = [int(i) for i in found[0].split('~')]
    if bound[0] > bound[1]:
        raise geo.AddressError(geo.__name__, rough_address)
    interval = int((bound[1] - bound[0] + 1) / settings.GEO_SAMPLES)
    samples = [i for i in range(bound[0], bound[1] + 1, interval)]
    for sample in samples:
        query_address = rough_address.replace(found[0], str(sample))
        gps_coordinates = geo.geocode(query_address, culture='zh-TW')["GPS"]
        if gps_coordinates["lat"] and gps_coordinates["lon"]:
            lat_results.append(gps_coordinates["lat"])
            lon_results.append(gps_coordinates["lon"])
    return {"lat": lat_results, "lon": lon_results}

def partition_geocode(con: sqlite3.Connection, cur: sqlite3.Cursor, quarter: str, county_cht: str):
    """ Geocode address of the same county in quarter fashion """
    cur.execute('''SELECT 土地區段位置或建物區門牌 FROM "{0}/TRX"
                   WHERE 縣市 = ?
                   GROUP BY 土地區段位置或建物區門牌;'''.format(quarter), (county_cht,))
    for address, in cur.fetchall():
        cur.execute('''SELECT GEO.編號
                       FROM "{0}/TRX" AS TRX, "{0}/GEO" AS GEO
                       WHERE TRX.編號 = GEO.編號
                       AND TRX.土地區段位置或建物區門牌 = ?
                       AND GEO.LAT_Avg ISNULL;'''.format(quarter), (address,))
        identities = cur.fetchall()
        if not identities:
            continue
        print("[%d] "%(len(identities)) + address)
        try:
            results = selective_geocode(address)
        except geo.AddressError:
            continue
        if len(results["lat"]) != 5 or len(results["lon"]) != 5:
            continue
        results["lat"].append(sum(results["lat"]) / len(results["lat"]))
        results["lon"].append(sum(results["lon"]) / len(results["lon"]))
        combined = [num for zipped in zip(results["lat"], results["lon"]) for num in zipped]
        values = [(tuple(combined) + identity) for identity in identities]
        cur.executemany('''UPDATE "{0}/GEO" SET
                               LAT_1 = ?, LON_1 = ?,
                               LAT_2 = ?, LON_2 = ?,
                               LAT_3 = ?, LON_3 = ?,
                               LAT_4 = ?, LON_4 = ?,
                               LAT_5 = ?, LON_5 = ?,
                               LAT_Avg = ?, LON_Avg = ?
                           WHERE 編號 = ?;'''.format(quarter), values)
        con.commit()

def main():
    """ Main Process """
    connection = sqlite3.connect(settings.__main_db__)
    cursor = connection.cursor()
    for prefix in COUNTY_PRI:
        county_cht = settings.alpha2cht(prefix)
        bitmask = 1 << (ord(prefix) - 65)
        cursor.execute('''SELECT quarter FROM {0}
                          WHERE (geocode_log & ?) != ?'''.format(IMPORTED_FOLDERS),
                       (bitmask, bitmask))
        quarters = [result[0] for result in cursor.fetchall()]
        for quarter in quarters:
            print("\n%s %s" %(quarter, county_cht))
            partition_geocode(connection, cursor, quarter, county_cht)
            cursor.execute('''UPDATE {0} SET geocode_log = (geocode_log | ?)
                              WHERE quarter = ?;'''.format(IMPORTED_FOLDERS),
                           (bitmask, quarter))
            connection.commit()
    connection.close()

if __name__ == "__main__":
    # clear terminal output
    if sys.platform.startswith("darwin"):
        os.system('clear')
    elif sys.platform.startswith("linux"):
        os.system('clear')
    elif sys.platform.startswith("win"):
        os.system('cls')

    # toggle between server and normal mode
    SERVER_RESTART_INTERVAL = 3600
    print("    Activating server mode causes geocoding process to automatically restart when")
    print("exception is encountered.\n")
    SERVER_MODE = True if (input("Activate server mode? [y/n]: ").lower() == "y") else False
    while SERVER_MODE:
        try:
            main()
        except Exception as e:
            print("\nCaught exception: \n%s\n" %(e), file=sys.stderr)
            print("Restart in %d seconds..." %(SERVER_RESTART_INTERVAL), end='', flush=True)
            time.sleep(SERVER_RESTART_INTERVAL)
            print()
    main()
