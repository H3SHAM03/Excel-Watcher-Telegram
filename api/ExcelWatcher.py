from http.server import BaseHTTPRequestHandler
import telebot
import requests
import pandas as pd
from io import BytesIO
import sys
import threading

BOT_TOKEN='8155782575:AAFSuF6eZfriFPuh7tFonfpRAI3p8Ks6UHU'
bot = telebot.TeleBot(BOT_TOKEN)
excel_links = []
messageID = []

def get_args(message):
    return message.split()[1:]

@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    bot.reply_to(message, "Howdy, how are you doing?")
    messageID.append(message.chat.id)

@bot.message_handler(commands=['add'])
def add_excel_link(message):
    try:
        link = get_args(message.text)[0]
        name = get_args(message.text)[1]
        response = requests.get(link)
        if response.status_code != 200:
            bot.reply_to(message,"Unable to download the file. Please check the link.")
        else:
            df = pd.read_excel(BytesIO(response.content))
            row_count = len(df.axes[0])
            excel_links.append({'name': name, 'link': link, 'row_count': row_count})
            bot.reply_to(message, f"File {name} added successfully")
    except Exception as e:
        print(e)
        bot.reply_to(message,"Usage: /add_excel <link> <name>")

def check_list():
    while True:
        for i in excel_links:
            response = requests.get(i['link'])
            df = pd.read_excel(BytesIO(response.content))
            if len(df.axes[0]) > i['row_count']:
                bot.send_message(messageID[0],f"Bad News!\nFile {i['name']} has been updated from {i['row_count']} to {len(df.axes[0])}")
            elif len(df.axes[0]) < i['row_count']:
                bot.send_message(messageID[0],f"Good News!\nFile {i['name']} has been updated from {i['row_count']} to {len(df.axes[0])}")
            i['row_count'] = len(df.axes[0])
                

@bot.message_handler(commands=['list'])
def links_list(message):
    text = ''
    for i,link in enumerate(excel_links):
        text = text + f'{i+1}. ' + f'Name: {link['name']}\nLink: {link['link']}\nNumber of rows: {link['row_count']}\n\n'
    if text != '':
        bot.reply_to(message,text)
    else:
        bot.reply_to(message,'List is empty')

@bot.message_handler(commands=['stop'])
def stop_bot(message):
    bot.reply_to(message, "Stopping the bot...")
    bot.stop_polling()
    sys.exit()

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','text/plain')
        self.end_headers()
        self.wfile.write('Working'.encode('utf-8'))
        t = threading.Thread(target=check_list)
        t.start()

        bot.infinity_polling()