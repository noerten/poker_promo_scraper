import datetime
import sqlite3
import urllib.request
from bs4 import BeautifulSoup

betsafe_promos_url = 'https://www.betsafe.com/en/specialoffers/'
triobet_promos_url = 'https://www.triobet.com/en/promotions/'
#despite 'poker' in guts' url, there are all promos
guts_promos_url = 'https://www.guts.com/en/poker/promotions'

def get_html(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urllib.request.urlopen(req).read()                             
    return webpage

def scrape_betsafe(html):
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
        promo_added = datetime.datetime.now()
        promo_room = 'betsafe'
        one_promo = (promo_title, promo_desc, promo_type, promo_link,
                     promo_image_link, promo_added, promo_room)
        betsafe_promos.append(one_promo)
        print(one_promo)
    return betsafe_promos

def scrape_triobet(html):
    soup = BeautifulSoup(html, "html.parser")
    section = soup.find('li', class_='promotion-list')
    triobet_promos = []
    for item in section.find_all('li', class_='promotion-container'):
        if item['class'][1] == 'odds': promo_type = 'sports'
        else: promo_type = item['class'][1]
        triobet_promos.append({
            'type' : promo_type,
            'title' : item.find('h2').string,
            'desc' : item.find('p').string,
            'link' : 'https://www.triobet.com'+item.a.get('href'),
            'image_link' : item.img.get('data-src'),
            'added' : datetime.datetime.now(),
            'room' : 'triobet'
            })
    return triobet_promos

def scrape_guts(html):
    soup = BeautifulSoup(html, "html.parser")
    div = soup.find('div', class_='promotions')
    guts_promos = []
    for item in div.find_all('div', class_='card'):
        guts_promos.append({
            'type' : item.a.get('href').split('/')[1],
            'title' : item.find('h2').get_text(strip=True),
            'desc' : item.find('p'),
            'link' : 'https://www.guts.com'+item.a.get('href'),
            'image_link' : item.img.get('src'),
            'added' : datetime.datetime.now(),
            'room' : 'guts'
            })
    return guts_promos

promos_urls = {betsafe_promos_url: scrape_betsafe,
               #triobet_promos_url: scrape_triobet,
               #guts_promos_url: scrape_guts,
               }

def work_with_db():
    conn = sqlite3.connect('stat.sqlite3')
    cur=conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS promos\
                (id INTEGER, added TEXT, type TEXT, title TEXT, desc TEXT,\
                link TEXT, image_link TEXT, room_id INTEGER)')
    cur.execute('CREATE TABLE IF NOT EXISTS rooms\
                (id INTEGER PRIMARY KEY, room TEXT)')

def main():
    promos = []
    for url in list(promos_urls.keys()):
        promos.append(promos_urls[url](get_html(url)))#list of dicts w promos
    print(promos)

if __name__ == '__main__':
    main()
