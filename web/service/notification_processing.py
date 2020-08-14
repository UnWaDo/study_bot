from config import GROUP_ID, VERIFICATION_RESPONSE, ACCESS_TOKEN, API_VERSION
import logging, requests
from datetime import datetime
from random import randint
import web.service.vk_api_connector as VK
from web.models import User, VKUser, IncomingMessage, OutgoingMessage
from web.models import STATUS_ADMIN, STATUS_MODERATOR, STATUS_UNKNOWN, STATUS
from web.service.messager import new_user_greeting, notify_on_status_change, approval_message, error_message
import re


def verification(data):
    if str(data.get('group_id')) == GROUP_ID:
        logging.info('Group %s was confirmed.', GROUP_ID)
        return VERIFICATION_RESPONSE
    logging.error('Confirmation failed. Expected %s, found %s', GROUP_ID, data.get('group_id'))
    return 'confirmation failed'

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
    command = re.search(r'задать уровень доступа (\w+) как (\w+)', message.text.lower())
    if command is not None:
        user = User.get(vk_id=message.from_id)
        if user.status != STATUS_ADMIN:
            error_message(user.vk_id, 'Недостаточный уровень доступа для выполнения команды.')
            return 'ok'
        login = command.group(1)
        changing_user = User.get(login=login)
        if changing_user is None:
            error_message(user.vk_id, 'Пользователя {} не существует.'.format(login))
            return 'ok'

        result = change_status(
            login=command.group(1),
            status=command.group(2)
        )
        if not result:
            error_message(user.vk_id, 'Некорректное указание кода уровня доступа.')
            return 'ok'

        approval_message(
            user.vk_id,
            'Пользователь {login} теперь имеет уровень доступа {status}'.format(
                login=changing_user.login,
                status=STATUS[changing_user.status]
            )
        )
        return 'ok'

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

def change_status(login, status):
    user = User.get(login=login)
    if status.lower() in ['u', 'unknown', 'unk', 'неопр', 'неизвестный']:
        user.set_status(STATUS_UNKNOWN)
    elif status.lower() in ['m', 'moderator', 'moder', 'модер', 'модератор']:
        user.set_status(STATUS_MODERATOR)
    elif status.lower() in ['a', 'admin', 'administrator', 'админ', 'администратор']:
        user.set_status(STATUS_ADMIN)
    else:
        return False
    notify_on_status_change(user)
    return True
