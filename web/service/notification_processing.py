from config import GROUP_ID, VERIFICATION_RESPONSE, ACCESS_TOKEN, API_VERSION
import logging, requests
from datetime import datetime
from random import randint
import web.service.vk_api_connector as VK
from web.models import User, VKUser, IncomingMessage, OutgoingMessage


def verification(data):
    if str(data.get('group_id')) == GROUP_ID:
        logging.info('Group %s was confirmed.', GROUP_ID)
        return VERIFICATION_RESPONSE
    logging.error('Confirmation failed. Expected %s, found %s', GROUP_ID, data.get('group_id'))
    return 'confirmation failed'

def new_user_greeting(user_id):
    user = VK.get_user(user_id)
    name = user['first_name']
    text = 'Добро пожаловать, {}! Для вывода справки напишите "Справка"'.format(name)

    message = OutgoingMessage(
        to_id=user_id,
        text=text
    )
    result = message.send()
    if not result:
        logging.error('Failed to send message to user %s.', user_id)


def new_message(data):
    message = IncomingMessage(
        from_id = data['object']['message']['from_id'],
        random_id = data['object']['message']['random_id'],
        text = data['object']['message']['text']
    )
    message.save()
    vk_user = VKUser.get(vk_id=message.from_id)
    if vk_user is None:
        vk_user = VKUser(user_id)
        vk_user.save()
        logging.info('New user with ID %s was added.', user_id)
        new_user_greeting(user_id)

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
