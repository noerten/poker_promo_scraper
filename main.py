import datetime
import json
import re
import sqlite3
import sys
import urllib.request

from bs4 import BeautifulSoup
import html5lib

#MPN
betsafe_promos_urls = ('https://www.betsafe.com/en/specialoffers/',)
triobet_promos_urls = ('https://www.triobet.com/en/promotions/',)
#despite 'poker' in guts' url, there are all promos
guts_promos_urls = ('https://www.guts.com/en/poker/promotions/',)
olybet_promos_urls = ('https://promo.olybet.com/com/sports/promotions/',
                      'https://promo.olybet.com/com/casino/promotions/',
                      'https://promo.olybet.com/com/poker/promotions/',
                      )
#pokerstars
pokerstars_promos_urls = ('https://www.pokerstars.com/poker/promotions/',)
#ipoker
betfred_promos_urls = (
                       'http://www.betfred.com/promotions/Sports',
                       'http://www.betfred.com/promotions/Casino',
                       'http://www.betfred.com/promotions/Lottery',
                       'http://www.betfred.com/promotions/Poker',
                       'http://www.betfred.com/promotions/Virtual',
                       'http://www.betfred.com/promotions/Bingo',
                       'http://www.betfred.com/games/promotions',
                       )
coral_promos_urls = ('http://www.coral.co.uk/lotto/offers/',
                     'http://www.coral.co.uk/poker/offers/',
                     'http://www.coral.co.uk/poker/tournaments/',
                     'http://www.coral.co.uk/gaming/promotions/',
                     'http://www.coral.co.uk/sports/offers/',
#uncommented doesnt work coz renders on client?                     
#                     'http://www.coral.co.uk/bingo/promotions/',
                     )
betfair_main_promos_urls = ('https://promos.betfair.com/sport',
                            'https://promos.betfair.com/arcade',
                            'https://promos.betfair.com/macau',
#uncommented coz diff structure and show only first dep bonuses
#                           'https://casino.betfair.com/promotions',
#uncommented coz diff structure and i dont use bingo promos
#                           'https://bingo.betfair.com/promotions',
                     )
betfair_poker_promos_urls = (
                             'https://poker.betfair.com/promotions',
                             )
#didnt add casino
mansion_promos_urls = (
                       'http://www.mansionpoker.com/promotions',
                       )

netbet_sports_promos_urls = (
                      'https://sportapi-sb.netbet.com/promotions',
                      )
netbet_poker_promos_urls = (
                      'https://poker.netbet.com/eu/promotions',
                      )
##didnt added casino coz didnt find api
netbet_casino_promos_urls = (
                      'https://casino.netbet.com/eu/promotions-en',
                      'https://vegas.netbet.com/en/promotion',
                      )
paddypower_poker_promos_urls = (
                          'https://api.paddypower.com/promotions/1.0/promotions/?channel=poker&category=324',
#                         'http://www.paddypower.com/bet/money-back-specials',
                       )
#didnt add sport and games
paddypower_casino_promos_urls = (
                                 'https://casino.paddypower.com/promotions',
                                 )
###############################################################################

def get_html(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        webpage = urllib.request.urlopen(req).read()
        return webpage
    except urllib.error.HTTPError as err:
        error_desc = 'HTTP Error %s: %s at URL %s' % (err.code, err.msg, url)
        return('error', error_desc)
        #raise

#must be before classes
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

class Room_Promos:
    def __init__(self, base_url, html):
        self.base_url = base_url
        self.room_promos = []
        self.soup = BeautifulSoup(html, "html.parser")
                
    def add_promo(self, promo):
        self.room_promos.append(promo)

class Promo:
    rooms = get_rooms()

    def __init__(self):
        self.ptype = None
        self.ptitle = None
        self.pdesc = None
        self.plink = None
        self.pimage_link = None
        self.proom = None
        
    def clear_promo_data(self, room, base_url):
        self.promo_room = Promo.rooms[room]
        if self.ptitle:
            self.ptitle = self.ptitle.strip()
        if self.pdesc:
            self.pdesc = self.pdesc.strip()
        if self.plink and not (self.plink.startswith("//") or self.plink.startswith("http")):
            self.plink = base_url+self.plink
        if self.pimage_link and not (self.pimage_link.startswith("//") or self.pimage_link.startswith("http")):
            self.pimage_link = base_url+self.pimage_link
        self.one_promo = (self.ptitle, self.pdesc, self.ptype,
                          self.plink, self.pimage_link, self.proom)
        
def scrape_betsafe(html, rooms, promos_url):
    room = Room_Promos(None, html)
    cont = room.soup.find(id='ArticleGrid')
    for item in cont.find_all(id='PromotionItem'):
        promo = Promo()
        promo.ptype = item['class'][1].split('Category')[0]
        promo.ptitle = item.find(id='PromotionTitle').string
        promo.pdesc = item.find(id='PromotionDescriptionText').string
        promo.plink = item.a.get('href')
        promo.pimage_link = item.find(id='PromotionImage').get('src')
        promo.clear_promo_data('betsafe', room.base_url) 
        room.add_promo(promo.one_promo)
    return room.room_promos

def scrape_triobet(html, rooms, promos_url):
    room = Room_Promos('https://www.triobet.com', html)
    cont = room.soup.find('li', class_='promotion-list')
    for item in cont.find_all('li', class_='promotion-container'):
        promo = Promo()
        if item['class'][1] == 'odds': promo.ptype = 'sports'
        else: promo.ptype = item['class'][1]
        promo.ptitle = item.find('h2').string
        promo.pdesc = item.find('p')
        for element in promo.pdesc.find_all('br'):
            element.replace_with(" ")
        promo.pdesc = promo.pdesc.get_text()
        promo.plink = item.a.get('href')
        promo.pimage_link = item.img.get('data-src')
        promo.clear_promo_data('triobet', room.base_url) 
        room.add_promo(promo.one_promo)
    return room.room_promos

def scrape_guts(html, rooms, promos_url):
    room = Room_Promos('https://www.guts.com', html)
    cont = room.soup.find('div', class_='promotions')
    for item in cont.find_all('div', class_='card'):
        promo = Promo()
        promo.ptype = item.a.get('href').split('/')[1]
        promo.ptitle = item.find('h2').get_text(strip=True)
        promo.pdesc = item.find('p')
        br_part = promo.pdesc.br.extract().string
        wo_br = promo.pdesc.string
        if br_part:
            promo.pdesc = wo_br + "\n" + br_part
        else:
            promo.pdesc = wo_br
        promo.plink = item.a.get('href')
        promo.pimage_link = item.img.get('src')
        promo.clear_promo_data('guts', room.base_url) 
        room.add_promo(promo.one_promo)
    return room.room_promos

def scrape_olybet(html, rooms, promos_url):
    soup = BeautifulSoup(html, "html.parser")
    div = soup.find(id='offers-list')
    olybet_promos = []
    promo_type = promos_url.split('/')[-3]
    for item in div.find_all('li'):
        promo_title = item.find('span').string
        promo_desc = None
        promo_link = 'https://promo.olybet.com'+item.a.get('href')
        promo_image_link = item.img.get('src')
        promo_room = rooms['guts']
        one_promo = (promo_title, promo_desc, promo_type, promo_link,
                     promo_image_link, promo_room)
        olybet_promos.append(one_promo)
    return olybet_promos

def scrape_pokerstars(html, rooms, promos_url):
    base_url = 'https://www.pokerstars.com'
    soup = BeautifulSoup(html, "html.parser")
    section = soup.find(id='portalWrap')
    room_promos = []
    for item in section.find_all('div', class_='promoPromotion'):
        promo_type = item.a.get('href').split('/')[1]
        if promo_type == 'vip':
            promo_type = 'poker'
        promo_title = item.find('div', class_='promoThumbText')
        promo_title.span.extract()
        promo_title = promo_title.get_text()
        promo_desc = None
        promo_link = item.a.get('href')
        promo_image_link = item.img.get('src')
        promo_room = rooms['pokerstars']
        promo_title, promo_desc, promo_link, promo_image_link = clear_promo_data(
            promo_title, promo_desc, promo_link, promo_image_link, base_url)
        one_promo = (promo_title, promo_desc, promo_type, promo_link,
                     promo_image_link, promo_room)
        room_promos.append(one_promo)
    return room_promos

def scrape_coral(html, rooms, promos_url):
    base_url = 'http://www.coral.co.uk'
    soup = BeautifulSoup(html, "html.parser")
    section = soup.find('div', class_='bigpromotionContainer')
    room_promos = []
    promo_type = promos_url.split('/')[3]
    if promo_type == 'gaming': promo_type = 'casino'
    for item in section.find_all('div', class_='item'):
        promo_title = item.h1.string
        try:
            promo_desc = item.p.string
        except:
            promo_desc = None
            print(promo_title+' has mistake in description')
        promo_link = None
        promo_image_link = item.img.get('src').split('?')[0]
        promo_room = rooms['coral']
        promo_title, promo_desc, promo_link, promo_image_link = clear_promo_data(
            promo_title, promo_desc, promo_link, promo_image_link, base_url)
        one_promo = (promo_title, promo_desc, promo_type, promo_link,
                     promo_image_link, promo_room)
        room_promos.append(one_promo)
    return room_promos

def scrape_betfred(html, rooms, promos_url):
    base_url = 'http://www.betfred.com'
    soup = BeautifulSoup(html, "html.parser")
    section = soup.find(id='centerbar')
    promo_type = promos_url.split('/')[-1].lower()
    if not section:
        section = soup.find('div', class_='wrapper_976')
        promo_type = 'casino'
    room_promos = []
    for item in section.find_all('div', class_='promoholder'):
        if len(item.get_text())<40:
            continue #to get rid of empty div's in games
        promo_title = item.h2.string
        promo_desc_p = item.find_all('p')
        promo_desc = []
        for p in promo_desc_p:
            if p.get_text().lower() != 'terms & conditions':
                promo_desc.append(p.get_text())
        promo_desc = '\n'.join(promo_desc)
        promo_link = None
        if item.find_all('div', class_='button'):
            for button in item.find_all('div', class_='button'):
                button_text = button.a.string.lower()
                if button_text.startswith('more detail'):
                    promo_link = button.a.get('href')
        promo_image_link = item.img.get('src')
        promo_room = rooms['betfred']
        promo_title, promo_desc, promo_link, promo_image_link = clear_promo_data(
            promo_title, promo_desc, promo_link, promo_image_link, base_url)
        one_promo = (promo_title, promo_desc, promo_type, promo_link,
                     promo_image_link, promo_room)
        room_promos.append(one_promo)
    return room_promos

def scrape_betfair_main(html, rooms, promos_url):
    #using html5lib coz of mistakes? on the page and html.parser doesnt find
    # needed tags
    soup = BeautifulSoup(html, "html5lib")
    room_promos = []
    base_url = 'https://promos.betfair.com'
    container = soup.find('ul', class_="promo-hub")
    #find only direct children
    for item in container.find_all('li',recursive=False):
        promo_type = item['class'][0].split('-')[1]
        if promo_type == 'sportsbook':
            promo_type == 'sports'
            promo_title = item.find('p', class_='promo-title').string
            promo_desc = item.find('span').string
        else:
            promo_title = item.find('span').string
            try:
                promo_desc = item.find('p').string
            except AttributeError:
                promo_desc = None
        promo_link = item.a.get('href')
        promo_image_cont = item.find('div', class_='banner-image')['style']
        promo_image_link = re.findall("\('(.*?)'\)", promo_image_cont)[0]
        promo_room = rooms['betfair']
        promo_title, promo_desc, promo_link, promo_image_link = clear_promo_data(
            promo_title, promo_desc, promo_link, promo_image_link, base_url)
        one_promo = (promo_title, promo_desc, promo_type, promo_link,
                     promo_image_link, promo_room)
        room_promos.append(one_promo)
    return room_promos

def scrape_betfair_poker(html, rooms, promos_url):
    base_url = 'https://poker.betfair.com'
    soup = BeautifulSoup(html, "html5lib")
    room_promos = []
    promo_type = 'poker'
    container = soup.find(id="right-column")
    for item in container.find_all('li'):
        promo_title = item.find('h2', class_='promotion-caption').string
        promo_desc = item.find('span', class_='promotion-title-caption').p.string
        promo_link = item.a.get('href')
        promo_image_link = item.img.get('src')
        promo_room = rooms['betfair']
        promo_title, promo_desc, promo_link, promo_image_link = clear_promo_data(
            promo_title, promo_desc, promo_link, promo_image_link, base_url)
        one_promo = (promo_title, promo_desc, promo_type, promo_link,
                     promo_image_link, promo_room)
        room_promos.append(one_promo)
    return room_promos

def scrape_mansion(html, rooms, promos_url):
    base_url = 'http://www.mansionpoker.com'
    soup = BeautifulSoup(html, "html.parser")
    room_promos = []
    promo_type = 'poker'
    container = soup.find(id="inner_content")
    for item in container.find_all('div', class_='simple-node-wrapper'):
        promo_title = item.find('div', class_='content').h3.string
        promo_desc = item.find('p').get_text()
        promo_link = item.a.get('href')
        promo_image_link = item.img.get('src')
        promo_room = rooms['mansion']
        promo_title, promo_desc, promo_link, promo_image_link = clear_promo_data(
            promo_title, promo_desc, promo_link, promo_image_link, base_url)
        one_promo = (promo_title, promo_desc, promo_type, promo_link,
                     promo_image_link, promo_room)
        room_promos.append(one_promo)
    return room_promos

def scrape_netbet_sports(html, rooms, promos_url):
    base_url = 'https://sport.netbet.com'
    json_obj = json.loads(html.decode("utf-8")[7:-2])
    soup = BeautifulSoup(json_obj['html'], "html.parser")
    room_promos = []
    promo_type = 'sports'
    for item in soup.find_all('div', class_='freeContentBlock'):
        promo_title = item.h2.string
        promo_desc = item.p.string
        promo_link = item.a.get('href')
        promo_image_link = item.find('div', class_='contentPage').img.get('src')
        promo_room = rooms['netbet']
        promo_title, promo_desc, promo_link, promo_image_link = clear_promo_data(
            promo_title, promo_desc, promo_link, promo_image_link, base_url)
        one_promo = (promo_title, promo_desc, promo_type, promo_link,
                     promo_image_link, promo_room)
        room_promos.append(one_promo)
    return room_promos

def scrape_netbet_poker(html, rooms, promos_url):
    base_url = promos_url.rsplit('/', 2)[0]
    soup = BeautifulSoup(html, "html.parser")
    room_promos = []
    promo_type = promos_url.split('.')[0].split('/')[-1].lower()
    container = soup.find(class_="sect-white")
    for item in container.find_all('div', class_='promo-box'):
        promo_title = item.find('h2', class_='info-offer').span.string
        promo_desc = item.find('div', class_='offer-details').p.string
        promo_link = item.a.get('href')
        promo_image_link = item.img.get('src')
        promo_room = rooms['netbet']
        promo_title, promo_desc, promo_link, promo_image_link = clear_promo_data(
            promo_title, promo_desc, promo_link, promo_image_link, base_url)
        one_promo = (promo_title, promo_desc, promo_type, promo_link,
                     promo_image_link, promo_room)
        room_promos.append(one_promo)
    return room_promos

def scrape_netbet_casino(html, rooms, promos_url):
    base_url = promos_url.rsplit('/', 2)[0]
    soup = BeautifulSoup(html, "html5lib")
    room_promos = []
    promo_type = promos_url.split('.')[0].split('/')[-1].lower()
    container = soup.find(id="promo_content")
    for item in container.find_all('div', class_='promoBlk'):
        promo_title = item.h3.string
        promo_desc = item.p.string
        promo_link = item.a.get('href')
        promo_image_link = item.img.get('src')
        promo_room = rooms['netbet']
        promo_title, promo_desc, promo_link, promo_image_link = clear_promo_data(
            promo_title, promo_desc, promo_link, promo_image_link, base_url)
        one_promo = (promo_title, promo_desc, promo_type, promo_link,
                     promo_image_link, promo_room)
        room_promos.append(one_promo)
        print(one_promo)
    return room_promos

def scrape_paddypower_poker(html, rooms, promos_url):
    base_url = ''
    json_obj = json.loads(html.decode("utf-8"))['data']
    room_promos = []
    promo_type = 'poker'
    for item in json_obj:
        if item['attributes']['promotion_hide']['attribute_value'] == '0':
            promo_title = item['name']
            promo_desc_soup = BeautifulSoup(item['attributes']['promotion_description']['attribute_value'], "html.parser")
            for element in promo_desc_soup.find_all('li'):
                element.insert(0, '\n')
            for element in promo_desc_soup.find_all('p'):
                element.insert(0, '\n')
            promo_desc = promo_desc_soup.get_text()
            promo_link = 'http://poker.paddypower.com/promotions/#/'+item['alias']
            promo_image_link = ('http://i.ppstatic.com/content/poker/'+
                                item['attributes']['promotion_media']['attribute_value'])
            promo_room = rooms['paddypower']
            promo_title, promo_desc, promo_link, promo_image_link = clear_promo_data(
                promo_title, promo_desc, promo_link, promo_image_link, base_url)
            one_promo = (promo_title, promo_desc, promo_type, promo_link,
                         promo_image_link, promo_room)
            room_promos.append(one_promo)
    return room_promos

def scrape_paddypower_casino(html, rooms, promos_url):
    base_url = ''
    soup = BeautifulSoup(html, "html.parser")
    room_promos = []
    promo_type = 'casino'
    container = soup.find(id="content_frame")
    for item in container.find_all('div', class_='promotion-list-item'):
        promo_link = item.a.get('href')
        promo_html = get_html(promo_link)
        promo_soup = BeautifulSoup(promo_html, "html.parser")
        inner_cont = promo_soup.find(id='content_frame').find('div', class_='promotion_details')
        promo_title = inner_cont.h2.string
        for tag in inner_cont.find_all(True):
            tag.replaceWith('')    
        promo_desc = inner_cont.get_text()
        promo_image_link = item.img.get('src')
        promo_room = rooms['paddypower']
        promo_title, promo_desc, promo_link, promo_image_link = clear_promo_data(
            promo_title, promo_desc, promo_link, promo_image_link, base_url)
        one_promo = (promo_title, promo_desc, promo_type, promo_link,
                     promo_image_link, promo_room)
        room_promos.append(one_promo)
    return room_promos

def testing():
    a = (True, False)
    return a[0]

if not testing():  
    promos_urls = {
                   betsafe_promos_urls: scrape_betsafe,
                   triobet_promos_urls: scrape_triobet,
                   guts_promos_urls: scrape_guts,
                   olybet_promos_urls: scrape_olybet,
                   pokerstars_promos_urls: scrape_pokerstars,
                   betfred_promos_urls: scrape_betfred,
                   betfair_main_promos_urls: scrape_betfair_main,
                   betfair_poker_promos_urls: scrape_betfair_poker,
                   coral_promos_urls: scrape_coral,
                   mansion_promos_urls: scrape_mansion,
                   netbet_sports_promos_urls: scrape_netbet_sports,
                   netbet_poker_promos_urls: scrape_netbet_poker,
                   netbet_casino_promos_urls: scrape_netbet_casino,#doesnt work
                   paddypower_poker_promos_urls: scrape_paddypower_poker,
                   }
else:
    promos_urls = {
                   guts_promos_urls: scrape_guts,
                   }
print('testing: '+str(testing()))

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
#    print(inactive_promos)
#new promos with image, inactive without
    return [new_promos, inactive_promos]

def print_tv(a):
    print('type: '+str(type(a)))
    print(a)
    
def main():
    scraped_promos = []
    error_counter = 0
    create_tables()
    print('tables ok')
    rooms = get_rooms()
    for urls in list(promos_urls.keys()):
        for url in urls:
            html = get_html(url)
            if html[0] == 'error':
                error_counter = error_counter + 1
                print(html[1])
                continue
            else:       
                i=promos_urls[urls](html, rooms, url)
                scraped_promos = scraped_promos+i
                print(str(len(i))+' promos were scraped from '+url)
    #delete dublicates
    scraped_promos = set(scraped_promos)    
    print('in total '+str(len(scraped_promos))+' promos were scraped from '\
          +str(len(promos_urls))+' websites')
    #print(scraped_promos)
    base_promos = get_promos()
    print('there are '+str(len(base_promos))+' active promotions in db')
    #compared_promos equals to [new_promos, inactive_promos]
    compared_promos = compare_promos(base_promos, scraped_promos)
    print('there are '+str(error_counter)+' mistakes')
    print('there are '+str(len(compared_promos[0]))+' new promotions and '+\
          str(len(compared_promos[1]))+' inactive promotions')
    print('new promotions:')
    for i in compared_promos[0]:
        print(i)
        print('---')
    ##########################
    if testing() == True or error_counter > 0:
        print('exiting and not saving to db coz testing == true or there are url mistakes')
        sys.exit()
    print('inactive promotions:')
    for i in compared_promos[1]:
        print(i)
    insert_promos(compared_promos)
    print('end')


if __name__ == '__main__':
    main()


####
#find all id
#    result = []
#    for tag in soup.findAll(True,{'id':True}) :
#        result.append(tag['id'])
