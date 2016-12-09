import datetime
import sqlite3
import sys

def get_rooms():
    conn = sqlite3.connect('pps.sqlite3')
    with conn:
        cur=conn.cursor()
        cur.execute("SELECT * FROM rooms")
        rows = cur.fetchall()
        rooms = {}
        if rows:
            for row in rows:
                rooms[row[1]] = row[0]
        return rooms
    
def create_tables():
    rooms = (
        ("betsafe",),
        ("triobet",),
        ("guts",),
        ("olybet",),
        ("pokerstars",),
        ("betfred",),
        ("betfair",),
        ("coral",),
        ("mansion",),
        ("netbet",),
        ("paddypower",),
        ("bet365",),
        ("boyle",),
        ("iron",),
        ("titan",),
        ("william_hill",),
        ("winner",),
        ("32red",),
        ("betvictor",),
        ("888",),
        ("tonybet",),
        ("party",),
        ("natural8",),
        ("unibet",),
        ("tigergaming",),
        ("betonline",),
        )
    conn = sqlite3.connect('pps.sqlite3')
    with conn:
        conn.execute('pragma foreign_keys=ON')
        cur=conn.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS rooms\
                    (id INTEGER PRIMARY KEY, name TEXT, UNIQUE(name))')
        cur.execute('CREATE TABLE IF NOT EXISTS promos\
                    (id INTEGER PRIMARY KEY, title TEXT, desc TEXT, type TEXT,\
                    link TEXT, image_link TEXT,\
                    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,\
                    room_id INTEGER NOT NULL, is_active INTEGER\
                    DEFAULT 1, FOREIGN KEY(room_id) REFERENCES rooms(id))')
        cur.executemany("INSERT OR IGNORE INTO rooms(name) VALUES(?)", rooms)

def get_promos():
    conn = sqlite3.connect('pps.sqlite3')
    with conn:
        cur=conn.cursor()
        cur.execute("SELECT title, desc, type, link, room_id\
                    FROM promos WHERE is_active = 1")
        promos = cur.fetchall()
        return promos

def insert_promos(compared_promos):
    new_promos = compared_promos[0]
    inactive_promos = compared_promos[1]
    inactive_ids = []
    conn = sqlite3.connect('pps.sqlite3')
    with conn:
        cur=conn.cursor()
        if new_promos:
            cur.executemany('INSERT INTO promos (title, desc, type, link,\
                            image_link, room_id) VALUES (?,?,?,?,?,?)', new_promos)
        if inactive_promos:
            cur.execute("SELECT id, title, desc, type, link, room_id\
                        FROM promos WHERE is_active = 1")
            rows = cur.fetchall()
            promos_dict = {}
            for row in rows:
                promo_wo_id = (row[1], row[2], row[3], row[4], row[5],)
                promo_id = row[0]
                promos_dict[promo_wo_id] = promo_id
            for i in inactive_promos:
                if i in promos_dict:
                    inactive_ids.append(promos_dict[i])
            inactive_ids = tuple(inactive_ids)
            if len(inactive_ids) == 1:
                cur.execute('UPDATE promos SET is_active = 0 WHERE id = {ii}'\
                            .format(ii=inactive_ids[0]))
            else:
                cur.execute('UPDATE promos SET is_active = 0 WHERE id IN {ii}'\
                            .format(ii=inactive_ids))
#dont know why this doent work, upperr one works            
#            cur.executemany('UPDATE promos SET is_active = 0 WHERE id IN ?', inactive_ids)

def compare_promos(base_promos, scraped_promos):
    #base wo image, scraped with
    new_promos = []
    inactive_promos = []
    scraped_promos_wo_image = []
    for i in scraped_promos:
        #coz image links sometimes change esp for betfred
        wo_image=i[:4]+(i[-1],)
        scraped_promos_wo_image.append(wo_image)
        if wo_image not in base_promos:
            new_promos.append(i)
    for i in base_promos:
        if i not in scraped_promos_wo_image:
            inactive_promos.append(i)
#new promos with image, inactive without
    return [new_promos, inactive_promos]

def print_tv(a):
    print('type: '+str(type(a)))
    print(a)

def print_exit(a):
    print(a)
    sys.exit()
