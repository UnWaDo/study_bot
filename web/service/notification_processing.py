from config import GROUP_ID, VERIFICATION_RESPONSE, ACCESS_TOKEN, API_VERSION
import logging, requests
from datetime import datetime
from random import randint
import web.service.vk_api_connector as VK
from web.models import User, VKUser, IncomingMessage, OutgoingMessage
from web.models import STATUS_ADMIN, STATUS_MODERATOR, STATUS_UNKNOWN, STATUS, ACCESS_GROUP
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
    l_text = message.text.lower()
    vk_user = VKUser.get(vk_id=message.from_id)
    if vk_user is None:
        vk_user = VKUser(message.from_id)
        vk_user.save()
        logging.info('New user with ID %s was added.', vk_user.vk_id)
        new_user_greeting(message.from_id)
        return 'ok'
    command = re.search(r'задать уровень доступа (\w+) как (\w+)', l_text)
    if command is None:
        command = re.search(r'set access level of (\w+) as (\w+)', l_text)
    if command is not None:
        user = User.get(vk_id=message.from_id)
        if not validate_user(user):
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

    if l_text in ['помощь', 'справка', 'help', 'manual', 'man']:
        help_message(vk_user.vk_id)
        return 'ok'

    if l_text in ['access level', 'access levels', 'al', 'уровень доступа', 'уровни доступа', 'уд', 'статусы']:
        info_access_level(vk_user.vk_id)
        return 'ok'

    command = re.search(r'пользоват\w+ (\w+)', l_text)
    if command is None:
        command = re.search(r'user\w+ (\w+)', l_text)
    if command is not None:
        if not validate_user(vk_user):
            return 'ok'

        category = ''
        if command.group(1) in ['вк', 'vk', 'вконтакте']:
            category = 'vk'
        elif command.group(1) in ['бд', 'bd', 'база']:
            category = 'bd'
        elif command.group(1) in ['все', 'оба', 'both', 'all']:
            category = 'vkbd'
        else:
            error_message(vk_user.vk_id, 'Необходимо указать категорию пользователей (БД или ВК).')
        user_list(vk_user.vk_id, category)

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

def validate_user(user, allowed=ACCESS_GROUP):
    if user.status in allowed:
        return True
    else:
        error_message(user.vk_id, 'Недостаточный уровень доступа для выполнения команды.')
        return False

def help_message(vk_id):
    user = User.get(vk_id=vk_id)
    vk_user = User.get(vk_id=vk_id)
    text = ('Это бот для расписаний и прочей информации.' +
        'Пока что его функционал весьма ограничен,' +
        'но впоследствии будет реализовано больше различных функций.' +
        'На текущий момент Вы можете использовать следующие команды: \n' +
        '— Справка: выводит текст данной справки. \n' +
        '— Уровни доступа: более подробная информация о системе с уровнями доступа. \n' +
        '— Информация: (в разработке) выводит последнее информационное сообщение. \n')
    moder_level = ('Далее перечислены функции, доступные только Модераторам и Администраторам. \n' +
        '— Пользователи ВК: выводит список людей, которые писали боту и доступны для написания сообщений. \n' +
        '— Пользователи БД: выводит список людей, зарегистрированных в базе. \n')
    admin_level = ('Далее перечислены функкции, доступные только Администраторам. \n' +
        '— Задать уровень доступа *login* как *access_level*.')
    if user.status in ACCESS_GROUP or vk_user.status in ACCESS_GROUP:
        text += moder_level
    if user.status == STATUS_ADMIN or vk_user.status == STATUS_ADMIN:
        text += admin_level
    OutgoingMessage(
        to_id=vk_id,
        text=text
    ).send()

def info_access_level(vk_id):
    text = ('На текущий момент реализовано три уровня доступа. \n' +
        '— Администратор (A): имеет право на внесение изменений в уровень доступа других людей,' +
        'а также обладает другими правами, доступными остальным пользователям.\n' +
        '— Модератор (M): имеет право на просмотр списка зарегистрированных пользователей и на добавление информации (в разработке). \n' +
        '— Обычный пользователь (U): не имеет прав, кроме как писать боту.')
    OutgoingMessage(
        to_id=vk_id,
        text=text
    ).send()

def user_list(vk_id, category):
    text = ''
    if 'bd' in category:
        bd_users = User.get_all()
        text += 'Пользователи базы: \n'
        for user in bd_users:
            text += '— @id{vk_id} ({login}): уровень доступа — {access_level}. \n'.format(
                vk_id=user.vk_id,
                login=user.login,
                access_level=STATUS[user.status]
            )
    if 'vk' in category:
        vk_users = VKUser.get_all()
        text += 'Пользователи ВК: \n'
        for user in vk_users:
            text += '— @id{vk_id} (Пользователь {id}): уровень доступа — {access_level}. \n'.format(
                vk_id=user.vk_id,
                id=user.id,
                access_level=STATUS[user.status]
            )
    OutgoingMessage(
        to_id=vk_id,
        text=text
    ).send()
