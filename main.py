import datetime
import json
import re
import sqlite3
import sys
import urllib.request

from bs4 import BeautifulSoup
import html5lib

#ipoker
#bet365 only poker
bet365_poker_promos_urls = ('http://poker.bet365.com/promotions/en',)
betfair_main_promos_urls = ('https://promos.betfair.com/sport',
                            'https://promos.betfair.com/arcade',
                            'https://promos.betfair.com/macau',
#uncommented coz diff structure and show only first dep bonuses
#                           'https://casino.betfair.com/promotions',
#uncommented coz diff structure
#                           'https://bingo.betfair.com/promotions',
                            )
betfair_poker_promos_urls = ('https://poker.betfair.com/promotions',)
betfred_promos_urls = ('http://www.betfred.com/promotions/Sports',
                       'http://www.betfred.com/promotions/Casino',
                       'http://www.betfred.com/promotions/Lottery',
                       'http://www.betfred.com/promotions/Poker',
                       'http://www.betfred.com/promotions/Virtual',
                       'http://www.betfred.com/promotions/Bingo',
                       'http://www.betfred.com/games/promotions',)
boyle_poker_promos_urls = ('http://poker.boylesports.com/promotions',
                           'http://poker.boylesports.com/tournaments',)
coral_promos_urls = ('http://www.coral.co.uk/lotto/offers/',
                     'http://www.coral.co.uk/poker/offers/',
                     'http://www.coral.co.uk/poker/tournaments/',
                     'http://www.coral.co.uk/gaming/promotions/',
                     'http://www.coral.co.uk/sports/offers/',
#uncommented doesnt work coz renders on client? found api, to add                    
#                     'http://www.coral.co.uk/bingo/promotions/',
                     )
iron_promos_urls = (
                          'http://www.ironbet.com/promotions',
                          'http://www.ironpoker.com/promotions',
                          )
#didnt add casino
mansion_promos_urls = ('http://www.mansionpoker.com/promotions',)
##didnt added casino coz didnt find api
netbet_casino_promos_urls = (
                      'https://casino.netbet.com/eu/promotions-en',
                      'https://vegas.netbet.com/en/promotion',
                      )
netbet_poker_promos_urls = (
                      'https://poker.netbet.com/eu/promotions',
                      )
netbet_sports_promos_urls = (
                      'https://sportapi-sb.netbet.com/promotions',
                      )
#didnt add sport and games
paddypower_casino_promos_urls = (
                                 'https://casino.paddypower.com/promotions',
                                 )
paddypower_poker_promos_urls = (
                          'https://api.paddypower.com/promotions/1.0/promotions/?channel=poker&category=324',
#                         'http://www.paddypower.com/bet/money-back-specials',
                       )
#MPN
betsafe_promos_urls = ('https://www.betsafe.com/en/specialoffers/',)
#despite 'poker' in guts' url, there are all promos
guts_promos_urls = ('https://www.guts.com/en/poker/promotions/',)
olybet_promos_urls = ('https://promo.olybet.com/com/sports/promotions/',
                      'https://promo.olybet.com/com/casino/promotions/',
                      'https://promo.olybet.com/com/poker/promotions/',)
triobet_promos_urls = ('https://www.triobet.com/en/promotions/',)
#pokerstars
pokerstars_promos_urls = ('https://www.pokerstars.com/poker/promotions/',)
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
    def __init__(self, base_url, html, parser="html.parser"):
        self.base_url = base_url
        self.room_promos = []
        self.soup = BeautifulSoup(html, parser)
                
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
        self.proom = Promo.rooms[room]
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
    room = Room_Promos('https://promo.olybet.com', html)
    cont = room.soup.find(id='offers-list')
    for item in cont.find_all('li'):
        promo = Promo()
        promo.ptype = promos_url.split('/')[-3]
        promo.ptitle = item.find('span').string
        promo.plink = item.a.get('href')
        promo.pimage_link = item.img.get('src')
        promo.clear_promo_data('olybet', room.base_url) 
        room.add_promo(promo.one_promo)
    return room.room_promos

def scrape_pokerstars(html, rooms, promos_url):
    room = Room_Promos('https://www.pokerstars.com', html)
    cont = room.soup.find(id='portalWrap')
    for item in cont.find_all('div', class_='promoPromotion'):
        promo = Promo()
        promo.ptype = item.a.get('href').split('/')[1]
        if promo.ptype == 'vip':
            promo.ptype = 'poker'
        promo.ptitle = item.find('div', class_='promoThumbText')
        promo.ptitle.span.extract()
        promo.ptitle = promo.ptitle.get_text()
        promo.plink = item.a.get('href')
        promo.pimage_link = item.img.get('src')
        promo.clear_promo_data('pokerstars', room.base_url) 
        room.add_promo(promo.one_promo)
    return room.room_promos

def scrape_coral(html, rooms, promos_url):
    room = Room_Promos(None, html)
    cont = room.soup.find('div', class_='bigpromotionContainer')
    for item in cont.find_all('div', class_='item'):
        promo = Promo()
        promo.ptype = promos_url.split('/')[3]
        if promo.ptype == 'gaming': promo.ptype = 'casino'
        promo.ptitle = item.h1.string
        try:
            promo.pdesc = item.p.string
        except:
            print(promo.ptitle+' has mistake in description')
        promo.pimage_link = item.img.get('src').split('?')[0]
        promo.clear_promo_data('coral', room.base_url) 
        room.add_promo(promo.one_promo)
    return room.room_promos

def scrape_betfred(html, rooms, promos_url):
    room = Room_Promos('http://www.betfred.com', html)
    cont = room.soup.find(id='centerbar')
    if not cont:
        cont = room.soup.find('div', class_='wrapper_976')
    for item in cont.find_all('div', class_='promoholder'):
        promo = Promo()
        if len(item.get_text())<40:
            continue #to get rid of empty div's in games
        promo.ptype = promos_url.split('/')[-1].lower()
        if promo.ptype == 'promotions':
            promo.ptype = 'casino'
        promo.ptitle = item.h2.string
        promo_desc_p = item.find_all('p')
        promo_desc = []
        for p in promo_desc_p:
            if p.get_text().lower() != 'terms & conditions':
                promo_desc.append(p.get_text())
        promo.pdesc = '\n'.join(promo_desc)
        if item.find_all('div', class_='button'):
            for button in item.find_all('div', class_='button'):
                button_text = button.a.string.lower()
                if button_text.startswith('more detail'):
                    promo.plink = button.a.get('href')
        promo.pimage_link = item.img.get('src')
        promo.clear_promo_data('betfred', room.base_url) 
        room.add_promo(promo.one_promo)
    return room.room_promos

def scrape_betfair_main(html, rooms, promos_url):
    #using html5lib coz of mistakes? on the page and html.parser doesnt find
    # needed tags
    room = Room_Promos('https://promos.betfair.com', html, "html5lib")
    cont = room.soup.find('ul', class_="promo-hub")
    #find only direct children
    for item in cont.find_all('li',recursive=False):
        promo = Promo()
        promo.ptype = item['class'][0].split('-')[1]
        if promo.ptype == 'sportsbook':
            promo.ptype == 'sports'
            promo.ptitle = item.find('p', class_='promo-title').string
            promo.pdesc = item.find('span').string
        else:
            promo.ptitle = item.find('span').string
            try:
                promo.pdesc = item.find('p').string
            except AttributeError:
                promo.pdesc = None
        promo.plink = item.a.get('href')
        promo_image_cont = item.find('div', class_='banner-image')['style']
        promo.pimage_link = re.findall("\('(.*?)'\)", promo_image_cont)[0]
        promo.clear_promo_data('betfair', room.base_url) 
        room.add_promo(promo.one_promo)
    return room.room_promos

def scrape_betfair_poker(html, rooms, promos_url):
    room = Room_Promos('https://poker.betfair.com', html, "html5lib")
    cont = room.soup.find(id="right-column")
    for item in cont.find_all('li'):
        promo = Promo()
        promo.ptype = 'poker'
        promo.ptitle = item.find('h2', class_='promotion-caption').string
        promo.pdesc = item.find('span', class_='promotion-title-caption').p.string
        promo.plink = item.a.get('href')
        promo.pimage_link = item.img.get('src')
        promo.clear_promo_data('betfair', room.base_url) 
        room.add_promo(promo.one_promo)
    return room.room_promos

def scrape_mansion(html, rooms, promos_url):
    room = Room_Promos('http://www.mansionpoker.com', html)
    cont = room.soup.find(id="inner_content")
    for item in cont.find_all('div', class_='simple-node-wrapper'):
        promo = Promo()
        promo.ptype = 'poker'
        promo.ptitle = item.find('div', class_='content').h3.string
        promo.pdesc = item.find('p').get_text()
        promo.plink = item.a.get('href')
        promo.pimage_link = item.img.get('src')
        promo.clear_promo_data('mansion', room.base_url) 
        room.add_promo(promo.one_promo)
    return room.room_promos

def scrape_netbet_sports(html, rooms, promos_url):
    json_obj = json.loads(html.decode("utf-8")[7:-2])
    room = Room_Promos('https://sport.netbet.com', json_obj['html'])    
    for item in room.soup.find_all('div', class_='freeContentBlock'):
        promo = Promo()
        promo.ptype = 'sports'
        promo.ptitle = item.h2.string
        promo.pdesc = item.p.string
        promo.plink = item.a.get('href')
        promo.pimage_link = item.find('div', class_='contentPage').img.get('src')
        promo.clear_promo_data('netbet', room.base_url) 
        room.add_promo(promo.one_promo)
    return room.room_promos

def scrape_netbet_poker(html, rooms, promos_url):
    room = Room_Promos(promos_url.rsplit('/', 2)[0], html)    
    cont = room.soup.find(class_="sect-white")
    for item in cont.find_all('div', class_='promo-box'):
        promo = Promo()
        promo.ptype = promos_url.split('.')[0].split('/')[-1].lower()
        promo.ptitle = item.find('h2', class_='info-offer').span.string
        promo.pdesc = item.find('div', class_='offer-details').p.string
        promo.plink = item.a.get('href')
        promo.pimage_link = item.img.get('src')
        promo.clear_promo_data('netbet', room.base_url) 
        room.add_promo(promo.one_promo)
    return room.room_promos

def scrape_paddypower_poker(html, rooms, promos_url):
    room = Room_Promos(None, '')    
    json_obj = json.loads(html.decode("utf-8"))['data']
    for item in json_obj:
        if item['attributes']['promotion_hide']['attribute_value'] == '0':
            promo = Promo()
            promo.ptype = 'poker'
            promo.ptitle = item['name']
            promo_desc_soup = BeautifulSoup(item['attributes']['promotion_description']['attribute_value'], "html.parser")
            for element in promo_desc_soup.find_all('li'):
                element.insert(0, '\n')
            for element in promo_desc_soup.find_all('p'):
                element.insert(0, '\n')
            promo.pdesc = promo_desc_soup.get_text()
            promo.plink = 'http://poker.paddypower.com/promotions/#/'+item['alias']
            promo.pimage_link = ('http://i.ppstatic.com/content/poker/'+
                                item['attributes']['promotion_media']['attribute_value'])
            promo.clear_promo_data('paddypower', room.base_url) 
            room.add_promo(promo.one_promo)
    return room.room_promos

def scrape_paddypower_casino(html, rooms, promos_url):
    room = Room_Promos(promos_url.rsplit('/', 2)[0], html)    
    cont = room.soup.find(id="content_frame")
    for item in cont.find_all('div', class_='promotion-list-item'):
        promo = Promo()
        promo.ptype = 'casino'
        promo.plink = item.a.get('href')
        promo_html = get_html(promo.plink)
        promo_soup = BeautifulSoup(promo_html, "html.parser")
        inner_cont = promo_soup.find(id='content_frame').find('div', class_='promotion_details')
        promo.ptitle = inner_cont.h2.string
        ptag = None
        for tag in inner_cont.find_all(True):
            ptag = inner_cont.find('p')
            if ptag:
                break
            tag.replaceWith('')
        if not ptag:
            promo.pdesc = inner_cont.get_text()
        else:
            promo.pdesc = ptag.string
        promo.pimage_link = item.img.get('src')
        promo.clear_promo_data('paddypower', room.base_url) 
        room.add_promo(promo.one_promo)
    return room.room_promos

def scrape_bet365_poker(html, rooms, promos_url):
    base_url = None
    room = Room_Promos(base_url, html)    
    cont = room.soup.find(id="LinksContainer")
    for item in cont.find_all(id='ListElement'):
        promo = Promo()
        promo.ptype = promos_url.split('.')[0].split('/')[-1].lower()
        promo.ptitle = item.find('div', class_='infoTextContainer').get_text()
        promo.plink = item.a.get('href')
        promo_html = get_html(promo.plink)
        promo_soup = BeautifulSoup(promo_html, "html.parser")
        inner_cont = promo_soup.find('div', class_='RightColumn').find('p', class_='infoTextContainer ')
        promo.pdesc = inner_cont.get_text()
        promo_image_cont = item.find('div', class_='SubNavLinkImage')['style']
        promo.pimage_link = re.findall("\('(.*?)'\)", promo_image_cont)[0]
        promo.clear_promo_data('bet365', room.base_url) 
        room.add_promo(promo.one_promo)
    return room.room_promos

def scrape_boyle_poker(html, rooms, promos_url):
    base_url = 'http://poker.boylesports.com'
    room = Room_Promos(base_url, html)    
    cont = room.soup.find(id="promo-box-wrapper")
    for item in cont.find_all('div', class_='promo-box-li'):
        promo = Promo()
        promo.ptype = promos_url.split('.')[0].split('/')[-1].lower()
        promo.ptitle = item.find('div', class_='promo-box-li-title').span.get_text()
        promo.plink = item.a.get('href')
        promo.pdesc = item.find('div', class_='promo-box-li-content-txt').get_text()
        promo.pimage_link = item.img.get('src')
        promo.clear_promo_data('boyle', room.base_url) 
        room.add_promo(promo.one_promo)
    return room.room_promos

def scrape_iron(html, rooms, promos_url):
    base_url = promos_url.rsplit('/', 1)[0]
    room = Room_Promos(base_url, html)    
    cont = room.soup.find('div', class_='contWrapper')
    for item in cont.find_all('div', class_='promo_box'):
        promo = Promo()
        promo.plink = item.a.get('href')
        if base_url == 'http://www.ironpoker.com':
            promo.ptype = 'poker'
        else:
            if not 'casino' in promo.plink:
                promo.ptype = 'sports'
            else:
                promo.ptype = 'casino'
        promo.ptitle = item.find('a', class_='teaser_title').get_text()
        promo.pdesc = item.find('a', class_='promo_text').get_text()
        promo.pimage_link = item.img.get('src')
        promo.clear_promo_data('boyle', room.base_url) 
        room.add_promo(promo.one_promo)
    return room.room_promos

def testing():
    a = (True, False)
    return a[1]

if not testing():  
    promos_urls = {
                   betsafe_promos_urls: scrape_betsafe,
                   triobet_promos_urls: scrape_triobet,
                   guts_promos_urls: scrape_guts,
                   olybet_promos_urls: scrape_olybet,
                   pokerstars_promos_urls: scrape_pokerstars,
                   coral_promos_urls: scrape_coral,
                   betfred_promos_urls: scrape_betfred,
                   betfair_main_promos_urls: scrape_betfair_main,
                   betfair_poker_promos_urls: scrape_betfair_poker,
                   mansion_promos_urls: scrape_mansion,
                   netbet_sports_promos_urls: scrape_netbet_sports,
                   netbet_poker_promos_urls: scrape_netbet_poker,
                   paddypower_poker_promos_urls: scrape_paddypower_poker,
                   paddypower_casino_promos_urls: scrape_paddypower_casino,
                   bet365_poker_promos_urls: scrape_bet365_poker,
                   boyle_poker_promos_urls: scrape_boyle_poker,
                   iron_promos_urls: scrape_iron,
                   }
else:
    promos_urls = {
                   iron_poker_promos_urls: scrape_iron_poker,
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
        ("bet365",),
        ("boyle",),
        ("iron",),
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
