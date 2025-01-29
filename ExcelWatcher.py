import telebot
import requests
import pandas as pd
from io import BytesIO
import sys
import threading

BOT_TOKEN='8155782575:AAFSuF6eZfriFPuh7tFonfpRAI3p8Ks6UHU'
bot = telebot.TeleBot(BOT_TOKEN)
users = []
user_data = {}
owner_links = []

def get_args(message):
    return message.split()[1:]

@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    user_data[f'{message.from_user.id}'] = []
    bot.reply_to(message, f"Hi {message.from_user.first_name}, how are you doing?")
    if message.from_user.username not in users:
        users.append(message.from_user.username)
        save_data()

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
            user_data[f'{message.from_user.id}'].append({'name': name, 'link': link, 'row_count': row_count, 'username': message.from_user.username})
            bot.reply_to(message, f"File {name} added successfully")
            save_data()
    except Exception as e:
        print(e)
        bot.reply_to(message,"Usage: /add <link> <name>")

def check_list():
    while True:
        for key in list(user_data.keys()):
            for i in user_data[key]:
                try:
                    response = requests.get(i['link'])
                    df = pd.read_excel(BytesIO(response.content))
                    if len(df.axes[0]) > i['row_count']:
                        bot.send_message(key,f"Bad News!\nFile {i['name']} has been updated from {i['row_count']} to {len(df.axes[0])}")
                    elif len(df.axes[0]) < i['row_count']:
                        bot.send_message(key,f"Good News!\nFile {i['name']} has been updated from {i['row_count']} to {len(df.axes[0])}")
                    i['row_count'] = len(df.axes[0])
                except Exception as e:
                    print(e)
                

@bot.message_handler(commands=['list'])
def links_list(message):
    text = ''
    for i,link in enumerate(user_data[f'{message.from_user.id}']):
        text = text + f'{i+1}. ' + f'Name: {link["name"]}\nLink: {link["link"]}\nNumber of rows: {link["row_count"]}\n\n'
    if text != '':
        bot.reply_to(message,text)
    else:
        bot.reply_to(message,'List is empty')
    print(user_data)
    print(users)

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
            if i['name'] == name:
                user_data[f'{message.from_user.id}'].remove(i)
                bot.reply_to(message,f"File {name} removed successfully")
                save_data()
                return
        bot.reply_to(message,f"File {name} not found in list")
    except Exception as e:
        print(e)
        bot.reply_to(message,"Usage: /remove <name>")

def save_data():
    try:
        with open('user data.txt','w') as f:
            f.write(str(user_data))
    except Exception as e:
        print(e)

def read_data():
    try:
        f = open('user data.txt','r')
    except:
        open('user data.txt','x')
        f = open('user data.txt','r')
    data = f.read()
    global user_data
    if data == '':
        user_data = {}
        f.close()
    else:
        user_data = eval(data)
        f.close()        

read_data()
t = threading.Thread(target=check_list)
t.start()

bot.infinity_polling()
