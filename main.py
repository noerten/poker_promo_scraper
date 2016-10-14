import datetime
import sqlite3
import sys
import urllib.request
from bs4 import BeautifulSoup

betsafe_promos_url = 'https://www.betsafe.com/en/specialoffers/'
triobet_promos_url = 'https://www.triobet.com/en/promotions/'
#despite 'poker' in guts' url, there are all promos
guts_promos_url = 'https://www.guts.com/en/poker/promotions/'
pokerstars_promos_url = 'https://www.pokerstars.com/poker/promotions/'

def get_html(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urllib.request.urlopen(req).read()                             
    return webpage

def scrape_betsafe(html, rooms):
    soup = BeautifulSoup(html, "html.parser")
    grid = soup.find(id='ArticleGrid')
    betsafe_promos = []
    for item in grid.find_all(id='PromotionItem'):
        promo_type_tag = item['class'][1]
        promo_type = promo_type_tag.split('Category')[0]
        promo_title = item.find(id='PromotionTitle').string
        promo_desc = item.find(id='PromotionDescriptionText').string
        promo_link = item.a.get('href')
        promo_image_link = item.find(id='PromotionImage').get('src')
        promo_room = rooms['betsafe']
        one_promo = (promo_title, promo_desc, promo_type, promo_link,
                     promo_image_link, promo_room)
        betsafe_promos.append(one_promo)
    return betsafe_promos

def scrape_triobet(html, rooms):
    soup = BeautifulSoup(html, "html.parser")
    section = soup.find('li', class_='promotion-list')
    triobet_promos = []
    for item in section.find_all('li', class_='promotion-container'):
        if item['class'][1] == 'odds': promo_type = 'sports'
        else: promo_type = item['class'][1]
        promo_title = item.find('h2').string
        promo_desc = item.find('p').string
        promo_link = 'https://www.triobet.com'+item.a.get('href')
        promo_image_link = item.img.get('data-src')
        promo_room = rooms['triobet']
        one_promo = (promo_title, promo_desc, promo_type, promo_link,
                     promo_image_link, promo_room)
        triobet_promos.append(one_promo)
    return triobet_promos

def scrape_guts(html, rooms):
    soup = BeautifulSoup(html, "html.parser")
    div = soup.find('div', class_='promotions')
    guts_promos = []
    for item in div.find_all('div', class_='card'):
        promo_type = item.a.get('href').split('/')[1]
        promo_title = item.find('h2').get_text(strip=True)
        promo_desc = item.find('p')
        br_part = promo_desc.br.extract().string
        wo_br = promo_desc.string
        if br_part:
            promo_desc = wo_br + "\n" + br_part
        else:
            promo_desc = wo_br
        promo_link = 'https://www.guts.com'+item.a.get('href')
        promo_image_link = item.img.get('src')
        promo_room = rooms['guts']
        one_promo = (promo_title, promo_desc, promo_type, promo_link,
                     promo_image_link, promo_room)
        guts_promos.append(one_promo)
    return guts_promos

def scrape_pokerstars(html, rooms):
    soup = BeautifulSoup(html, "html.parser")
    section = soup.find(id='portalWrap')
    pokerstars_promos = []
    for item in section.find_all('div', class_='promoPromotion'):
        promo_type = item.a.get('href').split('/')[1]
        promo_title = item.find('div', class_='promoThumbText')
        promo_title.span.extract()
        promo_title = promo_title.get_text()
        promo_desc = None
        promo_link = 'https://www.pokerstars.com' + item.a.get('href')
        promo_image_link = 'https://www.pokerstars.com' + item.img.get('src')
        promo_room = rooms['pokerstars']
        one_promo = (promo_title, promo_desc, promo_type, promo_link,
                     promo_image_link, promo_room)
        pokerstars_promos.append(one_promo)
    return pokerstars_promos

promos_urls = {
               betsafe_promos_url: scrape_betsafe,
               triobet_promos_url: scrape_triobet,
               guts_promos_url: scrape_guts,
               pokerstars_promos_url: scrape_pokerstars,
               }

def create_tables():
    rooms = (
        ("betsafe",),
        ("triobet",),
        ("guts",),
        ("pokerstars",),
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

def get_promos():
    conn = sqlite3.connect('pps.sqlite3')
    with conn:
        cur=conn.cursor()
        cur.execute("SELECT title, desc, type, link, image_link, room_id\
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
            cur.execute("SELECT id, title, desc, type, link, image_link, room_id\
                        FROM promos WHERE is_active = 1")
            rows = cur.fetchall()
            promos_dict = {}
            for row in rows:
                promo_wo_id = (row[1], row[2], row[3], row[4], row[5], row[6])
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
    new_promos = []
    inactive_promos = []
    for i in scraped_promos:
        if i not in base_promos:
            new_promos.append(i)
    for i in base_promos:
        if i not in scraped_promos:
            inactive_promos.append(i)
#    print(inactive_promos)
    return [new_promos, inactive_promos]

def print_tv(a):
    print('type: '+str(type(a)))
    print(a)
    
def main():
    scraped_promos = []
    create_tables()
    print('tables ok')
    rooms = get_rooms()
    for url in list(promos_urls.keys()):
        i=promos_urls[url](get_html(url), rooms)
        scraped_promos = scraped_promos+i
        print(str(len(i))+' promos were scraped from '+url)
#    print(scraped_promos)
    print('in total '+str(len(scraped_promos))+' promos were scraped from '\
          +str(len(promos_urls))+' websites')
    base_promos = get_promos()
    print('there are '+str(len(base_promos))+' active promotions in db')
    #compared_promos equals to [new_promos, inactive_promos]
    compared_promos = compare_promos(base_promos, scraped_promos)
    print('there are '+str(len(compared_promos[0]))+' new promotions and '+\
          str(len(compared_promos[1]))+' inactive promotions')
    insert_promos(compared_promos)

if __name__ == '__main__':
    main()
