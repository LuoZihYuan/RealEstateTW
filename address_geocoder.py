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

IMPORTED_FOLDERS = "IMPORTED_FOLDERS"
COUNTY_PRI = ['A', 'B', 'D', 'E', 'F', 'H', 'C', 'G', 'I', 'J', 'K',\
              'M', 'N', 'O', 'P', 'Q', 'T', 'U', 'V', 'W', 'X', 'Z']

def selective_geocode(rough_address: str) -> dict:
    """ Gets the average GPS coordinates of the rough address interval """
    lat_results = []; lon_results = []
    found = re.findall(r"\d+~\d+", rough_address)
    if not found:
        return {"lat": lat_results, "lon": lon_results}
    bound = [int(i) for i in found[0].split('~')]
    interval = int((bound[1] - bound[0] + 1) / settings.GEO_SAMPLES)
    samples = [i for i in range(bound[0], bound[1] + 1, interval)]
    for sample in samples:
        query_address = rough_address.replace(found[0], str(sample))
        gps_coordinates = geo.geocode(query_address, culture='zh-TW')["GPS"]
        if gps_coordinates["lat"] and gps_coordinates["lon"]:
            lat_results.append(gps_coordinates["lat"])
            lon_results.append(gps_coordinates["lon"])
    if lat_results and lon_results:
        return {"lat": lat_results, "lon": lon_results}
    raise geo.AddressError(geo.__name__, rough_address)

def partition_geocode(c: sqlite3.Cursor, quarter: str, county_cht: str):
    """ Geocode address of the same county in quarter fashion """
    c.execute('''SELECT 土地區段位置或建物區門牌 FROM "{0}/TRX"
                 WHERE 縣市 = ?
                 GROUP BY 土地區段位置或建物區門牌;'''.format(quarter), (county_cht,))
    for address, in c.fetchall():
        c.execute('''SELECT GEO.編號
                     FROM "{0}/TRX" AS TRX, "{0}/GEO" AS GEO
                     WHERE TRX.編號 = GEO.編號
                     AND TRX.土地區段位置或建物區門牌 = ?
                     AND GEO.LAT_Avg ISNULL;'''.format(quarter), (address,))
        identities = c.fetchall()
        if not identities:
            continue
        results = selective_geocode(address)
        results["lat"].append(sum(results["lat"]) / len(results["lat"]))
        results["lon"].append(sum(results["lat"]) / len(results["lat"]))
        combined = [num for zipped in zip(results["lat"], results["lon"]) for num in zipped]
        values = [(tuple(combined) + identity) for identity in identities]
        c.executemany('''UPDATE "{0}/GEO" SET
                             LAT_1 = ?, LON_1 = ?,
                             LAT_2 = ?, LON_2 = ?,
                             LAT_3 = ?, LON_3 = ?,
                             LAT_4 = ?, LON_4 = ?,
                             LAT_5 = ?, LON_5 = ?,
                             LAT_Avg = ?, LON_Avg = ?
                         WHERE 編號 = ?;'''.format(quarter), values)
        c.execute("COMMIT;")

def main():
    """ Main Process """
    con = sqlite3.connect(settings.__main_db__)
    cur = con.cursor()
    for prefix in COUNTY_PRI:
        county_cht = settings.alpha2cht(prefix)
        bitmask = 1 << (ord(prefix) - 65)
        cur.execute("SELECT quarter FROM {0} WHERE (geocode_log & ?) != ?".format(IMPORTED_FOLDERS),
                    (bitmask, bitmask))
        quarters = [result[0] for result in cur.fetchall()]
        for quarter in quarters:
            print(quarter, county_cht)
            partition_geocode(cur, quarter, county_cht)
            cur.execute('''UPDATE {0} SET geocode_log = (geocode_log | ?)
                           WHERE quarter = ?;'''.format(IMPORTED_FOLDERS),
                        (bitmask, quarter))
            con.commit()
    con.close()

if __name__ == "__main__":
    main()
