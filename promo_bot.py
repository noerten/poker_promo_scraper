import time
import eventlet
import logging
import telebot
from time import sleep

import config
import main
from sub_db import get_rooms

bot = telebot.TeleBot(config.TG_TOKEN)

def update_promos():
    timeout = eventlet.Timeout(60)
    try:
        new_promos = main.main()
        return new_promos
    except eventlet.timeout.Timeout:
        #logging.warning('Got Timeout while retrieving VK JSON data. Cancelling...')
        return None
    finally:
        timeout.cancel()

def send_new_posts(promos):
    #(self.ptitle, self.pdesc,self.ptype,self.plink,pimage_link, self.proom)
    rooms = get_rooms()
    #to change from name: number to number:name
    inv_rooms = {v: k for k, v in rooms.items()}

    for item in promos:
#        msg = "<code>{proom}/{ptype}</code>\n<a href='{plink}'>{ptitle}</a>\n{pdesc}\n".format(
        msg = "<code>{proom}/{ptype}</code>\n<b>{ptitle}</b>\n{plink}\n{pdesc}\n".format(
            plink = item[3],
            proom = inv_rooms[item[5]],
            ptype = item[2],                                                          
            ptitle = item[0],
            pdesc = item[1],                                             
            )

        bot.send_message(config.TG_CHANNEL_NAME, msg, parse_mode='HTML', disable_web_page_preview=True)
#        bot.send_photo(config.TG_CHANNEL_NAME, item[4], disable_notification=True)

if __name__ == '__main__':
    promos = update_promos()
    send_new_posts(promos)
