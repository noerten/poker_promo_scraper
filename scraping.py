import concurrent.futures
import datetime
import json
import re
import sqlite3
import sys
import time
import urllib.request

from bs4 import BeautifulSoup
import html5lib

import settings
from sub_db import get_rooms

def get_html(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Chrome/54.0.2840.99'})
        webpage = urllib.request.urlopen(req).read()
        return webpage
    except urllib.error.HTTPError as err:
        error_desc = 'HTTP Error %s: %s at URL %s' % (err.code, err.msg, url)
        return('error', error_desc)
    except urllib.error.URLError as err:
        error_desc = 'URL Error: %s at URL %s' % (err.reason, url)
        return('error', error_desc)
    except ConnectionError as err:
        error_desc = 'Connection Error: %s at URL %s' % (sys.exc_info(), url)
        return('error', error_desc)

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
        a = ' -\r\n\t\xa0'
        if self.ptitle:
            self.ptitle = " ".join(self.ptitle.split())
            self.ptitle = self.ptitle.strip(a)
        if self.pdesc:
            self.pdesc = " ".join(self.pdesc.split())
            self.pdesc = self.pdesc.strip(a)
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
            if wo_br.endswith(('!', '.', '?')):
                promo.pdesc = wo_br + " " + br_part
            else:
                promo.pdesc = wo_br + ". " + br_part
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
        promo.pdesc = ' '.join(promo_desc)
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
        promo.clear_promo_data('iron', room.base_url) 
        room.add_promo(promo.one_promo)
    return room.room_promos

def scrape_titan(html, rooms, promos_url):
    base_url = promos_url.rsplit('/', 1)[0]
    room = Room_Promos(base_url, html)    
    cont = room.soup.find('div', class_='rounded_content').find_all('div', class_='grid_9', recursive=False)[-1]
    for item in cont.find_all('div', class_='promos'):
        promo = Promo()
        promo.plink = item.a.get('href')
        promo.ptype = 'poker'
        promo.ptitle = item.h3.p.string
        promo.pdesc = item.find('p', recursive=False).get_text()
        promo.pimage_link = item.img.get('src')
        promo.clear_promo_data('titan', room.base_url) 
        room.add_promo(promo.one_promo)
    return room.room_promos

def scrape_william_hill_poker(html, rooms, promos_url):
    base_url = promos_url.rsplit('/', 1)[0]
    room = Room_Promos(base_url, html)    
    cont = room.soup.find('div', id='pokerGrid')
    for item in cont.find_all('div', class_='pokerTourBoxHolder'):
        promo = Promo()
        promo.plink = item.a.get('href')
        if promo.plink and not (promo.plink.startswith("//") or promo.plink.startswith("http")):
            promo.plink = base_url+promo.plink
        promo.ptype = 'poker'
        promo.pdesc = item.find(class_='detailsWrapper').p.get_text()
        promo.pimage_link = item.img.get('src')
        promo_html = get_html(promo.plink)
        promo_soup = BeautifulSoup(promo_html, "html.parser")
        promo.ptitle = promo_soup.find(id='pokerTitleUnder').h1.string
        promo.clear_promo_data('william_hill', room.base_url) 
        room.add_promo(promo.one_promo)
    return room.room_promos

def scrape_winner_poker(html, rooms, promos_url):
    base_url = promos_url.rsplit('/', 1)[0]
    room = Room_Promos(base_url, html)    
    cont = room.soup.find('div', id='wnr_p_content')
    for item in cont.find_all('div', class_='promo'):
        promo = Promo()
        promo.ptitle = item.find('div', class_='txt').h4.string
        promo.plink = item.a.get('href')
        promo.ptype = 'poker'
        promo.pdesc = item.find('div', class_='txt').p.get_text()
        promo.pimage_link = item.img.get('src')
        promo.clear_promo_data('winner', room.base_url) 
        room.add_promo(promo.one_promo)
    return room.room_promos

def scrape_32red_poker(html, rooms, promos_url):
    base_url = promos_url.rsplit('/', 2)[0]
    room = Room_Promos(base_url, html)    
    cont = room.soup.find('div', id='content')
    for item in cont.find_all('div', class_='promoBox'):
        promo = Promo()
        promo.ptitle = item.find('h3').get_text()
        promo.plink = item.a.get('href')
        promo.ptype = 'poker'
        pdesc1 = item.find('h4').get_text()
        pdesc2 = item.find('p').get_text()
        promo.pdesc = pdesc1 + '\n' + pdesc2
        promo.pimage_link = item.img.get('src')
        promo.clear_promo_data('32red', room.base_url) 
        room.add_promo(promo.one_promo)
    return room.room_promos

def scrape_betvictor_poker(html, rooms, promos_url):
    base_url = promos_url.rsplit('/', 4)[0]
    room = Room_Promos(base_url, html)    
    cont = room.soup.find('div', class_='page_content')
    for item in cont.find_all('table'):
        promo = Promo()
        main_td = item.find_all('td')[-1]
        promo.ptitle = main_td.find('strong').get_text()
        promo.plink = main_td.a.get('href')
        promo.ptype = 'poker'
        main_td.strong.replaceWith('')
        promo.pdesc = main_td.get_text()
        promo.pimage_link = item.img.get('src')
        promo.clear_promo_data('betvictor', room.base_url) 
        room.add_promo(promo.one_promo)
    return room.room_promos

def scrape_888(html, rooms, promos_url):
    base_url = promos_url.rsplit('/', 1)[0]
    room = Room_Promos(base_url, html)    
    cont = room.soup.find('div', id='main-content-wrapper')
    for outer_item in cont.find_all('div', class_='lobby-list-tab'):
        for item in outer_item.ul.find_all('li', recursive=False):
            promo = Promo()
            if 'lobby-show-tab-0' in outer_item['class']:
                continue
            elif 'lobby-show-tab-1' in outer_item['class']:
                promo.ptype = 'poker'
            elif 'lobby-show-tab-2' in outer_item['class']:
                promo.ptype = 'casino'
            elif 'lobby-show-tab-3' in outer_item['class']:
                promo.ptype = 'sports'
            else:
                raise NameError('something wrong with 888 promo types')
            promo.ptitle = item.find('span', class_='table-cell').get_text()
            promo.plink = item.a.get('href')
            promo.pdesc = item.find('span', class_='item-description').get_text()
            promo.pimage_link = item.img.get('data-original')
            promo.clear_promo_data('888', room.base_url) 
            room.add_promo(promo.one_promo)
    return room.room_promos

def scrape_tonybet_poker(html, rooms, promos_url):
    base_url = promos_url.rsplit('/', 1)[0]
    room = Room_Promos(base_url, html)    
    cont = room.soup.find('div', class_='listSideImg')
    for item in cont.find_all(class_='row', recursive=False):
        promo = Promo()
        promo.ptitle = item.a.get_text()
        promo.plink = item.a.get('href')
        promo.ptype = 'poker'
        promo.pdesc = item.p.get_text()
        promo.pimage_link = item.img.get('src')
        promo.clear_promo_data('tonybet', room.base_url) 
        room.add_promo(promo.one_promo)
    return room.room_promos

def scrape_party_poker(html, rooms, promos_url):
    base_url = promos_url.rsplit('/', 2)[0]
    room = Room_Promos(base_url, html)    
    cont = room.soup.find('div', id='main-content')
    for item in cont.find_all(class_='box'):
        promo = Promo()
        promo.ptitle = item.h3.get_text()
        promo.plink = item.a.get('href')
        promo.ptype = 'poker'
        promo.pdesc = item.find('div', class_='contentBox').get_text()
        promo.pimage_link = item.img.get('src')
        promo.clear_promo_data('party', room.base_url) 
        room.add_promo(promo.one_promo)
    return room.room_promos

def scrape_natural8(html, rooms, promos_url):
    base_url = promos_url.rsplit('/', 1)[0]
    room = Room_Promos(base_url, html)    
    cont = room.soup.find('div', class_='rock_margin_30')
    for item in cont.find_all(class_='rock_main_event'):
        promo = Promo()
        promo.ptitle = item.h2.get_text()
        promo.plink = item.a.get('href')
        promo.ptype = 'poker'
        promo.pdesc = item.find('div', class_='rock_main_event_detail').find_all('p')[-1].string
        promo.pimage_link = item.img.get('src')
        promo.clear_promo_data('natural8', room.base_url) 
        room.add_promo(promo.one_promo)
    return room.room_promos

def scrape_unibet(html, rooms, promos_url):
    #no image, coz it src by js
    base_url = promos_url.rsplit('/', 1)[0]
    room = Room_Promos(base_url, html, "html5lib")    
    cont = room.soup.find('div', id='column-primary')
    for outer_item in cont.find_all('div', recursive=False):
        for item in outer_item.find_all('article', class_="list-element"):
            promo = Promo()
            promo.ptype = outer_item.h3.get_text().lower().split(' ')[0]
            promo.ptitle = item.find('h4', class_='headline').get_text()
            promo.plink = item.a.get('href')
            if promo.plink and not (promo.plink.startswith("//") or promo.plink.startswith("http")):
                promo.plink = base_url+promo.plink
            promo_html = get_html(promo.plink)
            promo_soup = BeautifulSoup(promo_html, "html.parser")
            promo_cont = promo_soup.find('div', id='column-primary')
            if promo_cont:
                promo.pdesc = promo_cont.find('p').get_text()
#            promo.pimage_link = promo_cont.img.get('src')
            promo.clear_promo_data('unibet', room.base_url) 
            room.add_promo(promo.one_promo)
    return room.room_promos

def scrape_tigergaming(html, rooms, promos_url):
    base_url = promos_url.rsplit('/', 1)[0]
    room = Room_Promos(base_url, html)    
    cont = room.soup.find('table', class_='views-view-grid')
    for item in cont.find_all('div', class_='promo-wrapper'):
        promo = Promo()
        promo.ptitle = item.p.span.strong.get_text()
        promo.plink = item.a.get('href')
        promo.ptype = 'poker'
        promo_desc_cont = item.p.span
        for tag in promo_desc_cont.find_all(True):
            tag.replaceWith('')
        promo_desc = promo_desc_cont.get_text()
        promo.pimage_link = item.img.get('src')
        for i in 'casino', 'sportsbook', 'racebook':
            if i in promo.plink:
                if i == 'casino':
                    promo.ptype = 'casino'
                else:
                    promo.ptype = 'sports'
        promo.clear_promo_data('tigergaming', room.base_url) 
        room.add_promo(promo.one_promo)
    return room.room_promos

def scrape_betonline(html, rooms, promos_url):
    base_url = promos_url.rsplit('/', 1)[0]
    room = Room_Promos(base_url, html)    
    cont = room.soup
    for item in cont.find_all('div', class_='promotion_item'):
        promo = Promo()
        promo.ptitle = item.h3.get_text()
        promo.plink = item.a.get('href')
        p_parent = item.parent.get('id')
        if p_parent == 'deposit' or p_parent == 'sportsbooksection' or p_parent == 'horses':
            promo.ptype = 'sports'
        elif p_parent == 'casino':
            promo.ptype = 'casino'
        elif p_parent == 'poker':
            promo.ptype = 'poker'
        else:
            promo.ptype = 'other'
        for tag in item.p.find_all(True):
            tag.replaceWith('')
        promo.pdesc = item.p.get_text()
        promo.pimage_link = item.img.get('src')
        promo.clear_promo_data('betonline', room.base_url) 
        room.add_promo(promo.one_promo)
    return room.room_promos

def print_tv(a):
    print('type: '+str(type(a)))
    print(a)

def print_exit(a):
    print(a)
    sys.exit()
    
####
#find all id
#    result = []
#    for tag in soup.findAll(True,{'id':True}) :
#        result.append(tag['id'])
