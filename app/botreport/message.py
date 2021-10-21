import re
import telegram

from django.db.models import Q
from django.db import connections

from common.multiservice_integrator import *
from botservice.settings import TELEGRAM_TOKEN, BOT_URL
from app.botreport.models import Contact, BotHeader, BotContent

bot = telegram.Bot(token=TELEGRAM_TOKEN)
URL = BOT_URL.format(TELEGRAM_TOKEN)

def proccess(data):
    """
    Function that receive a json request "data"
    """
    msg = msg_handler(data)

    if "contact" in data['message']:
        create_user(msg)
    # elif 'entities' in data['message']:   
    #     replace_keys = {'/':'', '_':' '}
    #     cmd_formated = cmd_formatter(data['message']['text'], replace_keys, True)
    #     if 'start' in cmd_formated:
    #         login(data)
    
    else:
        login(msg)

def cmd_formatter(string, replacements, ignore_case=False):
    if ignore_case:
        def normalize_old(s):
            return s.lower()
        re_mode = re.IGNORECASE
    else:
        def normalize_old(s):
            return s
        re_mode = 0
    replacements = {normalize_old(key): val for key, val in replacements.items()}
    rep_sorted = sorted(replacements, key=len, reverse=True)
    rep_escaped = map(re.escape, rep_sorted)
    pattern = re.compile('|'.join(rep_escaped), re_mode)
    return pattern.sub(lambda match: replacements[normalize_old(match.group(0))], string)

def callback(cmd):
    """
    Get a command name as parameter and return command name id
    """
    try:
        cmd_name = BotHeader.objects.get(name=cmd)
        return cmd_name.id
    except:
       return False

def query_handler(cmd_id):
    """
    Receive a command id as parameter and return sql query related with the specif command
    """
    query = BotContent.objects.get(header_id=cmd_id)
    cur = connections['default'].cursor()
    cur.execute(query.sql)
    report = cur.fetchall()
    cur.close()
    return report

def msg_handler(data):
    """
    Receive a json request "data" then return a user dict "msg" with user credentials
    """
    user_id = data['message']['from']['id']

    if 'first_name' in data['message']['from']:
        first_name = data['message']['from']['first_name']
    else:
        first_name = ''

    if 'last_name' in data['message']['from']:
        last_name = data['message']['from']['last_name']
    else:
        last_name = ''
    
    msg = {
        'user_id': user_id,
        'first_name': first_name,
        'last_name': last_name,
    }

    if 'contact' in data['message']:
        msg['phone_number'] = data['message']['contact']['phone_number']
    return msg

def msg_login(msg):
    """
    Create a button in order to get the user phone number
    """
    reply_markup = telegram.ReplyKeyboardMarkup(
        [[telegram.KeyboardButton("Compartilhar contato \U0001F4DE ", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    bot.sendMessage(
        msg['user_id'], "Para continuar, por gentileza clique no botão abaixo para compartilhar o seu usuário e número do Telegram. \U0001F642", reply_markup=reply_markup
    )

def login(msg):
    try:
        contact = Contact.objects.get(user_id=msg['user_id']) 
        if contact:
            text = '*** Você já está cadastrado em nossa newsletter de alertas! \U0001F642 ***\n\n'
            bot.sendMessage(msg['user_id'], text)
            return True
        
    except Contact.DoesNotExist:
        text = '*** Olá! \U0001F642 Você precisa se cadastrar em nosso BOT. Por gentileza realizar login. ***\n\n'
        bot.sendMessage(msg['user_id'], text)
        msg_login(msg)

def create_user(msg):
    """
    Create a user in botdb
    """
    orm = virtual_orm()

    if 'accounts_user' in orm:
        user = [ u for u in orm['accounts_user'] if u['phone_number'] == msg['phone_number'].replace('+','')]
        if len(user) > 0:
            contact = Contact(
                user_id=msg["user_id"],
                contact_id=user[0]["id"],
                first_name=user[0]["first_name"],
                last_name=user[0]["last_name"],
                phone_number=msg['phone_number'].replace('+',''),
                )
            
            try:
                contact.save(using='default')
                text = 'Seja bem-vindo {} {}, você foi cadastrado na lista de alertas do seu sistema IndustryCare \U0001F642'.format(msg['first_name'], msg['last_name'])
                bot.sendMessage(msg['user_id'], text)
            
            except Exception as e:
                print('Ocorreu um erro', e)
        else:
            bot.sendMessage(msg['user_id'], 'Sinto muito, mas este telefone não foi identificado em nossa base de dados.')
    else:
        bot.sendMessage(msg['user_id'], 'No momento não foi possível se cadastrar no BOT. Por gentileza, tente novamente mais tarde ou entre em contato com nosso suporte.')