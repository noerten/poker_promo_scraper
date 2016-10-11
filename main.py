import urllib.request
from bs4 import BeautifulSoup

betsafe_promos_url = 'https://www.betsafe.com/en/specialoffers/'
triobet_promos_url = 'https://www.triobet.com/en/promotions/'

promos_urls=[betsafe_promos_url, triobet_promos_url]

def get_html(url):
    response = urllib.request.urlopen(url)
    return response.read()

def parse(html):
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
        
    
def main():
    for url in promos_urls:
        print(parse(get_html(url)))

if __name__ == '__main__':
    main()
