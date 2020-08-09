from config import GROUP_ID, VERIFICATION_RESPONSE, ACCESS_TOKEN, API_VERSION
import logging, requests
from datetime import datetime
from random import randint
from web.service.vk_api_connector import send_message, get_user


def verification(data):
    if str(data.get('group_id')) == GROUP_ID:
        logging.info('Group %s was confirmed.', GROUP_ID)
        return VERIFICATION_RESPONSE
    logging.error('Confirmation failed. Expected %s, found %s', GROUP_ID, data.get('group_id'))
    return 'confirmation failed'

def new_message(data):
    user_id = data['object']['message']['from_id']
    if user_id == None:
        return 'no user defined'
    user = get_user(user_id)
    if user is None:
        return 'ok'
    name = user['first_name']
    mess_id = send_message(text, user_id)
    if mess_id is not None:
        print('user_id: {}, text: {}, message_id: {}'.format(user_id, text, mess_id))
    return 'ok'

def request_processing(data):
    type = data.get('type')
    if type == None:
        return 'type is not defined'
    elif type == 'confirmation':
        return verification(data)
    elif type == 'message_new':
        return new_message(data)
    else:
        return 'unrecognized message'
