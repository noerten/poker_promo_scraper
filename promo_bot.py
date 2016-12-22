import time
import logging
import telebot
from time import sleep

import config
import main
from sub_db import get_rooms

bot = telebot.TeleBot(config.TG_TOKEN)

def send_new_posts(promos):
    #(self.ptitle, self.pdesc,self.ptype,self.plink,pimage_link, self.proom)
    rooms = get_rooms()
    #to change from name: number to number:name
    inv_rooms = {v: k for k, v in rooms.items()}
    for item in promos:
        msg = "<code>{proom}/{ptype}</code>\n<b>{ptitle}</b>\n{plink}\n{pdesc}\n".format(
            plink = item[3],
            proom = inv_rooms[item[5]],
            ptype = item[2],                                                          
            ptitle = item[0],
            pdesc = item[1],                                             
            )
        bot.send_message(config.TG_CHANNEL_NAME, msg, parse_mode='HTML',
                         disable_web_page_preview=True)
#        bot.send_photo(config.TG_CHANNEL_NAME, item[4], disable_notification=True)

def run_bot():
    logging.info('[BOT] started scanning')
    promos = main.main()
    logging.info('[BOT] got reply from pps module')
    send_new_posts(promos)
    logging.info('[BOT] sent promos')

if __name__ == '__main__':
    # Избавляемся от спама в логах от библиотеки requests
    logging.getLogger('requests').setLevel(logging.CRITICAL)
    # Настраиваем наш логгер
    logging.basicConfig(format='[%(asctime)s] %(filename)s:%(lineno)d %(levelname)s - %(message)s', level=logging.INFO,
                        filename='bot_log.log', datefmt='%d.%m.%Y %H:%M:%S')
    if not config.SINGLE_RUN:
        while True:
            run_bot()
            # Пауза в 5 минуты перед повторной проверкой
            logging.info('[BOT] Script went to sleep.')
            time.sleep(60 * 5)
    else:
        run_bot()
    logging.info('[BOT] Script exited.\n')
