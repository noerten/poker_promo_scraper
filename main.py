import concurrent.futures
import datetime
import sys
import time

import scraping
import settings
import sub_db

#####################################
if not settings.testing():  
    promos_urls = {
                   settings.betsafe_promo_urls: scraping.scrape_betsafe,
                   settings.triobet_promo_urls: scraping.scrape_triobet,
                   settings.guts_promo_urls: scraping.scrape_guts,
                   settings.olybet_promo_urls: scraping.scrape_olybet,
                   settings.pokerstars_promo_urls: scraping.scrape_pokerstars,
                   settings.coral_promo_urls: scraping.scrape_coral,
                   settings.betfred_promo_urls: scraping.scrape_betfred,
                   settings.betfair_main_promo_urls: scraping.scrape_betfair_main,
                   settings.betfair_poker_promo_urls: scraping.scrape_betfair_poker,
                   settings.mansion_promo_urls: scraping.scrape_mansion,
                   settings.netbet_sports_promo_urls: scraping.scrape_netbet_sports,
                   settings.netbet_poker_promo_urls: scraping.scrape_netbet_poker,
                   settings.paddypower_poker_promo_urls: scraping.scrape_paddypower_poker,
                   settings.boyle_poker_promo_urls: scraping.scrape_boyle_poker,
                   settings.iron_promo_urls: scraping.scrape_iron,
                   settings.titan_promo_urls: scraping.scrape_titan,
                   settings.winner_poker_promo_urls: scraping.scrape_winner_poker,
                   settings._32red_poker_promo_urls: scraping.scrape_32red_poker,
                   settings.betvictor_poker_promo_urls: scraping.scrape_betvictor_poker,
                   settings._888_promo_urls: scraping.scrape_888,
                   settings.tonybet_poker_promo_urls: scraping.scrape_tonybet_poker,
                   settings.party_poker_promo_urls: scraping.scrape_party_poker,
                   settings.natural8_promo_urls: scraping.scrape_natural8,
                   settings.tigergaming_promo_urls: scraping.scrape_tigergaming,
#                   settings.betonline_promo_urls: scraping.scrape_betonline,
                   }
#function with get_html, that break multithreading 
    promos_urls_w_get = {
                   settings.paddypower_casino_promo_urls: scraping.scrape_paddypower_casino,
                   settings.bet365_poker_promo_urls: scraping.scrape_bet365_poker,
                   settings.william_hill_poker_promo_urls: scraping.scrape_william_hill_poker,
                   settings.unibet_promo_urls: scraping.scrape_unibet,
                   }
else:
    promos_urls = {
                   settings.unibet_promo_urls: scraping.scrape_unibet,
                   }
    promos_urls_w_get = {
                   }
print('testing: '+str(settings.testing()))

def unpack_dict(promos_urls):
    url_func_dict = {}
    for urls in promos_urls:
        for url in urls:
            url_func_dict[url] = promos_urls[urls]
    return url_func_dict

def scrape_rooms(url_func_dict, rooms, start_time, error_counter=0):
    scraped_promos = []
    prev_time = None
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        # Start the load operations and mark each future with its URL
        future_to_url = {executor.submit(scraping.get_html, u): u for u in url_func_dict}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            html = future.result()
            if html[0] == 'error':
                error_counter = error_counter + 1
                print(html[1])
                continue
            else:
                i=url_func_dict[url](html, rooms, url)
                scraped_promos.extend(i)
                print(str(len(i))+' promos were scraped from '+url)
            if not prev_time:
                prev_time = start_time
            print("url took", time.time() - prev_time, "sec to run")
            prev_time = time.time()
    return error_counter, scraped_promos

def main():
    sub_db.create_tables()
    print('tables ok')
    rooms = sub_db.get_rooms()
    start_time = time.time()
    #dict from promos_urls, where key - one url, value - scrape func
    url_func_dict = unpack_dict(promos_urls)
    error_counter, scraped_promos = scrape_rooms(url_func_dict, rooms, start_time, error_counter=0)
    url_func_w_get_dict = unpack_dict(promos_urls_w_get)
    error_counter_w_get, scraped_promos_w_get = scrape_rooms(url_func_w_get_dict, rooms, start_time, error_counter=0)
    error_counter = error_counter + error_counter_w_get
    scraped_promos = scraped_promos + scraped_promos_w_get
    print(len(scraped_promos))
    print("total scraping took", time.time() - start_time, "sec to run")
    #delete dublicates
    scraped_promos = set(scraped_promos)    
    print('in total '+str(len(scraped_promos))+' promos were scraped from '\
          +str(len(promos_urls))+' websites')
    #print(scraped_promos)
    base_promos = sub_db.get_promos()
    print('there are '+str(len(base_promos))+' active promotions in db')
    #compared_promos equals to [new_promos, inactive_promos]
    compared_promos = sub_db.compare_promos(base_promos, scraped_promos)
    print('there are '+str(error_counter)+' mistakes')
    print('there are '+str(len(compared_promos[0]))+' new promotions and '+\
          str(len(compared_promos[1]))+' inactive promotions')
    print('new promotions:')
    for i in compared_promos[0]:
        print(i)
        print('---')
    ##########################
    if settings.testing() == True or error_counter > 0:
        print('exiting and not saving to db coz testing == true or there are url mistakes')
        sys.exit()
    print('inactive promotions:')
    for i in compared_promos[1]:
        print(i)
    sub_db.insert_promos(compared_promos)
    print('end')
    print("total program took", time.time() - start_time, "sec to run")

if __name__ == '__main__':
    main()
