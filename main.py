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
    pass
    soup = BeautifulSoup(html, "html.parser")
    grid = soup.find(id='ArticleGrid')
    betsafe_promos = []
    for item in grid.find_all(id='PromotionItem'):
        promo_type_tag = item['class'][1]
        betsafe_promos.append({
            'promo_type' : promo_type_tag.split('Category')[0],
            'promo_title' : item.find(id='PromotionTitle').string,
            'promo_desc' : item.find(id='PromotionDescriptionText').string,
            'promo_link' : item.a.get('href'),
            'promo_image_link' : item.find(id='PromotionImage').get('src')
            })
    return betsafe_promos

def scrape_triobet(html):
    pass
    soup = BeautifulSoup(html, "html.parser")
    section = soup.find('li', class_='promotion-list')
    triobet_promos = []
    for item in section.find_all('li', class_='promotion-container'):
        triobet_promos.append({
            'promo_type' : item['class'][1],
            'promo_title' : item.find('h2').string,
            'promo_desc' : item.find('p').string,
            'promo_link' : 'https://www.triobet.com'+item.a.get('href'),
            'promo_image_link' : item.img.get('data-src')
            })
    return triobet_promos

def scrape_guts(html):
    soup = BeautifulSoup(html, "html.parser")
    div = soup.find('div', class_='promotions')
    guts_promos = []
    for item in div.find_all('div', class_='card'):
        guts_promos.append({
            'promo_type' : item.a.get('href').split('/')[1],
            'promo_title' : item.find('h2'),
            'promo_desc' : item.find('p'),
            'promo_link' : 'https://www.guts.com'+item.a.get('href'),
            'promo_image_link' : item.img.get('src')
            })
    return guts_promos

promos_urls = {betsafe_promos_url: scrape_betsafe,
               triobet_promos_url: scrape_triobet,
               guts_promos_url: scrape_guts,
               }

def main():
    for url in list(promos_urls.keys()):
        print(promos_urls[url](get_html(url)))

if __name__ == '__main__':
    main()
