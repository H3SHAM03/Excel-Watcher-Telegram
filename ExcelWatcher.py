import telebot
import requests
import pandas as pd
from io import BytesIO
import sys
import threading

BOT_TOKEN=''
bot = telebot.TeleBot(BOT_TOKEN)
user_data = {}
owner_links = []

def get_args(message):
    return message.split()[1:]

@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    user_data[f'{message.from_user.id}'] = []
    bot.reply_to(message, f"Hi {message.from_user.first_name}, how are you doing?")

@bot.message_handler(commands=['add'])
def add_excel_link(message):
    try:
        link = get_args(message.text)[0]
        name = get_args(message.text)[1]
        name = ''
        for i in get_args(message.text)[1:]:
            name += i
            if i != get_args(message.text)[-1]:
                name += ' '
        response = requests.get(link)
        if response.status_code != 200:
            bot.reply_to(message,"Unable to download the file. Please check the link.")
        else:
            df = pd.read_excel(BytesIO(response.content))
            row_count = len(df.axes[0])
            user_data[f'{message.from_user.id}'].append({'name': name, 'link': link, 'row_count': row_count, 'chatID': message.chat.id})
            bot.reply_to(message, f"File {name} added successfully")
    except Exception as e:
        print(e)
        bot.reply_to(message,"Usage: /add <link> <name>")

def check_list():
    while True:
        for key in list(user_data.keys()):
            for i in user_data[key]:
                response = requests.get(i['link'])
                df = pd.read_excel(BytesIO(response.content))
                if len(df.axes[0]) > i['row_count']:
                    bot.send_message(i['chatID'],f"Bad News!\nFile {i['name']} has been updated from {i['row_count']} to {len(df.axes[0])}")
                elif len(df.axes[0]) < i['row_count']:
                    bot.send_message(i['chatID'],f"Good News!\nFile {i['name']} has been updated from {i['row_count']} to {len(df.axes[0])}")
                i['row_count'] = len(df.axes[0])
                

@bot.message_handler(commands=['list'])
def links_list(message):
    text = ''
    for i,link in enumerate(user_data[f'{message.from_user.id}']):
        text = text + f'{i+1}. ' + f'Name: {link["name"]}\nLink: {link["link"]}\nNumber of rows: {link["row_count"]}\n\n'
    if text != '':
        bot.reply_to(message,text)
    else:
        bot.reply_to(message,'List is empty')

@bot.message_handler(commands=['remove'])
def remove_excel_link(message):
    try:
        name = get_args(message.text)[0]
        name = ''
        for i in get_args(message.text)[0:]:
            name += i
            if i != get_args(message.text)[-1]:
                name += ' '
        for i in user_data[f'{message.from_user.id}']:
                user_data[f'{message.from_user.id}'].remove(i)
                bot.reply_to(message,f"File {name} removed successfully")
                return
        bot.reply_to(message,f"File {name} not found in list")
    except Exception as e:
        print(e)
        bot.reply_to(message,"Usage: /remove <name>")
            

t = threading.Thread(target=check_list)
t.start()

bot.infinity_polling()
