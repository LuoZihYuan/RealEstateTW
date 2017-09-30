""" create sqlite3 database from csv file """
import os
import csv
import pprint
import sqlite3
import settings

__version__ = "0.1"
DATABASE_PATH = os.path.join(settings.__resources__, "registration.db")
IMPORTED_FOLDERS = "IMPORTED_FOLDERS"

FLOOR_CHT = ["", "一", "二", "三", "四", "五", "六", "七", "八", "九"]
def floor(txt: str) -> int:
    """ convert Chinese level into Arabic number """
    underground = True if txt[:2] == "地下" else False
    target = txt[2:-1] if underground else txt [:-1]
    units = target.split(sep="十")
    total = 0; exp = 1
    for unit in units[::-1]:
        if not unit and exp != 1:
            digit = 1
        else:
            try:
                digit = FLOOR_CHT.index(unit)
            except ValueError:
                return None
        total += (digit * exp)
        exp *= 10
    total = total if not underground else -total
    return total if total else None
def floor_all(lst: list) -> list:
    """ shortcut for converting a list of Chinese levels """
    numerals = [floor(txt) for txt in lst if floor(txt)]
    return sorted(numerals)

def init_DB(c: sqlite3.Cursor) -> str:
    """ initialize database with essential data tables """
    c.execute('''CREATE TABLE IF NOT EXISTS {0}(
                     quarter TEXT PRIMARY KEY,
                     createdAt TEXT NOT NULL
                 );'''.format(IMPORTED_FOLDERS))
    c.execute('''CREATE TABLE IF NOT EXISTS 建物型態(
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     type TEXT NOT NULL UNIQUE,
                     count INTEGER DEFAULT 0
                 );''')
    c.execute('''CREATE TABLE IF NOT EXISTS 主要用途(
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     type TEXT NOT NULL UNIQUE,
                     count INTEGER DEFAULT 0
                 );''')
    c.execute('''CREATE TABLE IF NOT EXISTS 主要建材(
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     type TEXT NOT NULL UNIQUE,
                     count INTEGER DEFAULT 0
                 );''')
    c.execute('''CREATE TABLE IF NOT EXISTS 都市土地使用分區(
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     type TEXT NOT NULL UNIQUE,
                     count INTEGER DEFAULT 0
                 );''')
    c.execute('''CREATE TABLE IF NOT EXISTS 非都市土地使用分區(
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     type TEXT NOT NULL UNIQUE,
                     count INTEGER DEFAULT 0
                 );''')
    c.execute('''CREATE TABLE IF NOT EXISTS 非都市土地使用編定(
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     type TEXT NOT NULL UNIQUE,
                     count INTEGER DEFAULT 0
                 );''')
    c.execute('''CREATE TABLE IF NOT EXISTS 車位類別(
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     type TEXT NOT NULL UNIQUE,
                     count INTEGER DEFAULT 0
                 );''')
    c.execute("SELECT quarter FROM {0}".format(IMPORTED_FOLDERS))
    return [t[0] for t in c.fetchall()]
def create_table(c: sqlite3.Cursor, prefix: str):
    """ create data tables with the same prefix """
    c.execute('''CREATE TABLE "{0}/TRX"(
                     編號 TEXT PRIMARY KEY,
                     縣市 TEXT NOT NULL CHECK(length(縣市) == 3),
                     鄉鎮市區 TEXT NOT NULL CHECK(length(鄉鎮市區) <= 4),
                     土地區段位置或建物區門牌 TEXT NOT NULL,
                     交易年月日 TEXT NOT NULL,
                     總價元 INTEGER NOT NULL,
                     單價每平方公尺 INTEGER,
                     親友間交易 INTEGER NOT NULL,
                     含增建 INTEGER NOT NULL
                 );'''.format(prefix))
    c.execute('''CREATE TABLE "{0}/GEO"(
                     編號 TEXT PRIMARY KEY,
                     GEO_1 REAL NOT NULL,
                     GEO_2 REAL NOT NULL,
                     GEO_3 REAL NOT NULL,
                     GEO_4 REAL NOT NULL,
                     GEO_5 REAL NOT NULL,
                     GEO_Avg REAL NOT NULL,
                     FOREIGN KEY(編號) REFERENCES "{0}/TRX"(編號)
                 );'''.format(prefix))
    c.execute('''CREATE TABLE "{0}/BUILD"(
                     編號 TEXT PRIMARY KEY,
                     總樓層數 INTEGER,
                     移轉層次 TEXT,
                     建物型態 INTEGER NOT NULL,
                     主要用途 INTEGER,
                     主要建材 INTEGER,
                     建築完成年月 TEXT,
                     建物移轉總面積平方公尺 INTEGER NOT NULL,
                     '建物現況格局-隔間' INTEGER NOT NULL,
                     '建物現況格局-房' INTEGER NOT NULL,
                     '建物現況格局-廳' INTEGER NOT NULL,
                     '建物現況格局-衛' INTEGER NOT NULL,
                     有無管理組織 INTEGER NOT NULL,
                     FOREIGN KEY(編號) REFERENCES "{0}/TRX"(編號),
                     FOREIGN KEY(建物型態) REFERENCES 建物型態(id),
                     FOREIGN KEY(主要用途) REFERENCES 主要用途(id),
                     FOREIGN KEY(主要建材) REFERENCES 主要建材(id)
                 );'''.format(prefix))
    c.execute('''CREATE TABLE "{0}/LAND"(
                     編號 TEXT PRIMARY KEY,
                     土地移轉總面積平方公尺 REAL NOT NULL,
                     都市土地使用分區 INTEGER,
                     非都市土地使用分區 INTEGER,
                     非都市土地使用編定 INTEGER,
                     FOREIGN KEY(編號) REFERENCES "{0}/TRX"(編號),
                     FOREIGN KEY(都市土地使用分區) REFERENCES 都市土地使用分區(id),
                     FOREIGN KEY(非都市土地使用分區) REFERENCES 非都市土地使用分區(id),
                     FOREIGN KEY(非都市土地使用編定) REFERENCES 非都市土地使用編定(id)
                 );'''.format(prefix))
    c.execute('''CREATE TABLE "{0}/PARK"(
                     編號 TEXT PRIMARY KEY,
                     車位類別 INTEGER,
                     車位移轉總面積平方公尺 REAL NOT NULL,
                     車位總價元 INTEGER NOT NULL,
                     FOREIGN KEY(編號) REFERENCES "{0}/TRX"(編號),
                     FOREIGN KEY(車位類別) REFERENCES 車位類別(id)
                 );'''.format(prefix))

def parse_csv(rdr: csv.DictReader, c: sqlite3.Cursor, prefix: str, county: str):
    """ insert csv into specified data table """
    for row in rdr:
        if "建物" not in row["交易標的"]:
            continue

        if row["鄉鎮市區"] == "fa72埔鄉":
            row["鄉鎮市區"] = "鹽埔鄉"
        elif row["鄉鎮市區"] == "金fa4b鄉":
            row["鄉鎮市區"] = "金峰鄉"
        try:
            c.execute('''INSERT INTO "{0}/TRX"
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);'''.format(prefix),
                      (row["編號"], county, row["鄉鎮市區"], row["土地區段位置或建物區門牌"],
                       row["交易年月日"], row["總價元"], row["單價每平方公尺"],
                       True if ("親" in row["備註"]) or ("友" in row["備註"]) else False,
                       True if "增建" in row["備註"] else False))
        except sqlite3.IntegrityError:
            pprint.pprint(row)
            raise
        numbers = floor_all([f for f in row["移轉層次"].split(sep="，") if f and f[-1] == "層"])
        num_str = ", ".join(str(number) for number in numbers)

        def exist_row(picked_row: csv.OrderedDict, fieldname: str):
            """ insert new type into specified table or increase count when already exists """
            if (not picked_row[fieldname]) or ("見" in picked_row[fieldname]):
                return
            c.execute("SELECT EXISTS(SELECT * FROM {0} WHERE type == ?);".format(fieldname),
                      (picked_row[fieldname],))
            if not c.fetchall()[0][0]:
                c.execute("INSERT INTO {0}(type) VALUES(?);".format(fieldname),
                          (picked_row[fieldname],))
            c.execute("UPDATE {0} SET count = count + 1 WHERE type = ?;".format(fieldname),
                      (picked_row[fieldname],))

        exist_row(row, "建物型態")
        exist_row(row, "主要用途")
        exist_row(row, "主要建材")
        c.execute('''INSERT INTO "{0}/BUILD" VALUES (
                         ?, ?, ?, (
                             SELECT id FROM 建物型態 WHERE type == ?
                         ), (
                             SELECT id FROM 主要用途 WHERE type == ?
                         ), (
                             SELECT id FROM 主要建材 WHERE type == ?
                         ), ?, ?, ?, ?, ?, ?, ?);'''.format(prefix),
                  (row["編號"], floor(row["總樓層數"]), num_str if num_str else None, row["建物型態"],
                   row["主要用途"], row["主要建材"], row["建築完成年月"], row["建物移轉總面積平方公尺"],
                   True if row["建物現況格局-隔間"] == "有" else False, row["建物現況格局-房"], row["建物現況格局-廳"],
                   row["建物現況格局-衛"], True if row["有無管理組織"] == "有" else False))

        exist_row(row, "都市土地使用分區")
        exist_row(row, "非都市土地使用分區")
        exist_row(row, "非都市土地使用編定")
        c.execute('''INSERT INTO "{0}/LAND" VALUES (
                         ?, ?, (
                             SELECT id FROM 都市土地使用分區 WHERE type == ?
                         ), (
                             SELECT id FROM 非都市土地使用分區 WHERE type == ?
                         ), (
                             SELECT id FROM 非都市土地使用編定 WHERE type == ?
                         ));'''.format(prefix),
                  (row["編號"], row["土地移轉總面積平方公尺"], row["都市土地使用分區"], row["非都市土地使用分區"],
                   row["非都市土地使用編定"]))

        exist_row(row, "車位類別")
        c.execute('''INSERT INTO "{0}/PARK" VALUES (
                             ?, (
                                 SELECT id FROM 車位類別 WHERE type == ?
                             ), ?, ?);'''.format(prefix),
                  (row["編號"], row["車位類別"], row["車位移轉總面積平方公尺"], row["車位總價元"]))

def main():
    """ Main Process """
    con = sqlite3.connect(DATABASE_PATH)
    cur = con.cursor()
    table_names = init_DB(cur)

    folder_names = next(os.walk(settings.__resources__))[1]
    for folder_name in folder_names:
        print(folder_name)
        folder_path = os.path.join(settings.__resources__, folder_name)
        if folder_name in table_names:
            continue
        cur.execute("BEGIN;") # Disable auto-commit
        create_table(cur, folder_name)
        file_names = os.listdir(folder_path)
        for file_name in file_names:
            (root, ext) = os.path.splitext(file_name)
            if (ext != ".CSV") or (not root.endswith("A")):
                continue
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, 'r', encoding='big5', errors='ignore') as fstream:
                reader = csv.DictReader(fstream)
                cnty_en = settings.CountyAlpha(root[0]).name
                cnty_cht = settings.CountyCht[cnty_en].value
                parse_csv(reader, cur, folder_name, cnty_cht)
        cur.execute("INSERT INTO {0} VALUES(?, CURRENT_TIMESTAMP)".format(IMPORTED_FOLDERS),
                    (folder_name,))
        cur.execute("COMMIT;")

if __name__ == "__main__":
    main()
