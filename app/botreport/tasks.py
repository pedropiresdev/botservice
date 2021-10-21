from __future__ import absolute_import
from datetime import datetime

import telegram
import json
import uuid

from botservice.settings import TELEGRAM_TOKEN, BOT_URL
from app.botreport.models import Contact
from common.error_handler import registry_errors
from common.multiservice_integrator import *

from celery import shared_task

bot = telegram.Bot(token=TELEGRAM_TOKEN)
URL = BOT_URL.format(TELEGRAM_TOKEN)

def send_alert():
    """
    """
    kwargs = { 'db_key': None, 'user_id': -2, 'request_md_id': str(uuid.uuid1()) }
   
    contact_list = [ c for c in Contact.objects.using('default')]

    if contact_list:
        alert_ocurrencies_result = verify_alerty_occurrencies()
        alert_ocurrencies = alert_ocurrencies_result[0]
        db = alert_ocurrencies_result[1]
        
        for alert in alert_ocurrencies:
            db_key = list(db.values())[0]
            kwargs['db_key'] = db_key

        if alert_ocurrencies:
            for c in [ c for c in contact_list if c.phone_number in alert_ocurrencies ]:
                
                try:
                    
                    param = { 'id_universal': str(uuid.uuid1()), 'id': c.contact_id, 'datetime_read_input': datetime.now(), 'send': False }

                    text = ' \u26A0 Olá! {} {}, Estes são seus últimos alertas \U0001F642'.format(c.first_name, c.last_name)
                    
                    kwargs['request_md_id'] = str(uuid.uuid1()) # Gerar um id para cada consulta que pode ser executada no BD
                    filter_messages = [ a for a in alert_ocurrencies[ c.phone_number ] if c.contact_id not in a[2] ]
                    
                    if len(filter_messages) == 0:
                        continue
                    
                    bot.sendMessage(c.user_id, text)
                    messages = [ '{} alerta(s) para {}\n\n'.format(a[0], a[-1]) for a in filter_messages ]
                    bot.sendMessage(c.user_id, str.join('\n', messages))

                    param['send'] = True

                    id_list = []
                    [ id_list.extend( f[1] ) for f in filter_messages ]
                    id_list = [ (d, c.contact_id, True) for d in id_list ]
                    
                    with connections[db[c.phone_number]].cursor() as cursor:
                        cursor.executemany('''
                            INSERT INTO public.alert_occurrence_status( alert_occurrence_id, user_id, status )
                            VALUES( %s, %s, %s )
                            ON CONFLICT DO NOTHING
                            ''', id_list)
                    
                except Exception as e:
                    registry_errors(kwargs, e)
                finally:
                    if param['send'] == True:
                        log_botservice(kwargs, param)

def verify_alerty_occurrencies():

    orm = virtual_orm()
    contact_list = [ c for c in Contact.objects.using('default').values('phone_number').distinct()]
    valid_numbers =  [ c['phone_number'] for c in contact_list ]
    results = {}
    id_list = {}
    try:
        if len( contact_list ) > 0 and 'accounts_user' in orm:
            dbs_phones = {}
            for o in orm['accounts_user']:
                if o['report_db'] not in dbs_phones:
                    dbs_phones[ o['report_db'] ] = []
                if o['phone_number'] in valid_numbers:
                    dbs_phones[ o['report_db'] ].append( o['phone_number'] )

            phone_db = { k['phone_number'] :  k['report_db'] for k in orm['accounts_user'] }
            dbs = list( set( [ phone_db[ c['phone_number'] ] for c in contact_list if c['phone_number'] in phone_db ] ) )
            for db in dbs:
                with connections[db].cursor() as cursor:
                    try:
                        cursor.execute(
                            """
                                SELECT
                                    COUNT(a.*),
                                    array_agg( a.id ),
                                    array_remove(array_agg( s.user_id ), null),
                                    c.alert_name

                                FROM alert_occurrence a
                                    LEFT JOIN alert_config c on c.id = a.config_id
                                    LEFT JOIN alert_occurrence_status s on s.alert_occurrence_id = a.id

                                WHERE a.datetime_read BETWEEN now() - interval '30 seconds' and now()

                                GROUP BY 4
                            """
                        )
                    except Exception as error:
                        print(error.args[0])
                        return error.args[0]

                    object_list = cursor.fetchall()

                for phones in dbs_phones[db]:
                    results[ phones ] = object_list

            return results, phone_db

       
    except Exception as error:
        print(error)

def log_botservice(kwargs, params):
    # request_headers = args[1]._request.headers
    log =  dict()
    log['datetime_read_input'] = params['datetime_read_input']
    del params['datetime_read_input']
    params['request_md_id'] = kwargs['request_md_id']
    try:
        timezone = 'America/Sao_Paulo'
        log['datetime_read_output'] = datetime.now()
        log['user_id'] = kwargs['user_id']
        log['host'] = 'localhost'
        log['path'] = 'system_notification/'
        log['agent'] = ''
        log['params'] = json.dumps(params)

        dbclient = kwargs['db_key']
        cur = connections[dbclient].cursor()
        cur.execute(f"SET TIME ZONE '{timezone}';")
        cur.execute('''
            INSERT INTO public.system_log(datetime_read_input, datetime_read_output, user_id, host, path, agent, params)
            VALUES (%(datetime_read_input)s, %(datetime_read_output)s, %(user_id)s, %(host)s, %(path)s, %(agent)s, %(params)s);
        ''', log)
        cur.close()
    except Exception as e:
        print('Falha ao registrar log ' + str(e))

@shared_task
def send_alerts_out():

    try:
        send_alert()
        print('Alerta enviado!')

    except Exception as error:
        print(error)