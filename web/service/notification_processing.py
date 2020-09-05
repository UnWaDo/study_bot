from config import GROUP_ID, VERIFICATION_RESPONSE, ACCESS_TOKEN, API_VERSION
import logging, requests
from datetime import datetime
from random import randint
import web.service.vk_api_connector as VK
from web.models import User, VKUser, IncomingMessage, OutgoingMessage
from web.models import STATUS_ADMIN, STATUS_MODERATOR, STATUS_UNKNOWN, STATUS, ACCESS_GROUP
from web.service.messager import new_user_greeting, notify_on_status_change, approval_message, error_message
from web.service.helper import validate_vk_user, is_week_even
import re


def verification(data):
    if str(data.get('group_id')) == GROUP_ID:
        logging.info('Group %s was confirmed.', GROUP_ID)
        return VERIFICATION_RESPONSE
    logging.error('Confirmation failed. Expected %s, found %s', GROUP_ID, data.get('group_id'))
    return 'confirmation failed'

def new_message(data):
    inc_message = IncomingMessage()
    inc_message.save(data['object']['message'])

    l_text = inc_message.message.text.lower()
    vk_user = inc_message.vk_user
    if vk_user is None:
        vk_user = VKUser(inc_message.from_id)
        vk_user.save()
        logging.info('New user with ID %s was added.', vk_user.vk_id)
        new_user_greeting(vk_user)
        return 'ok'
    command = re.search(r'задать уровень доступа (\w+) как (\w+)', l_text)
    if command is None:
        command = re.search(r'set access level of (\w+) as (\w+)', l_text)
    if command is not None:
        change_status(
            caller=vk_user,
            subj_id=command.group(1),
            status=command.group(2)
        )
        return 'ok'

    if l_text in ['помощь', 'справка', 'help', 'manual', 'man']:
        help_message(vk_user)
        return 'ok'

    if l_text in ['access level', 'access levels', 'al', 'уровень доступа', 'уровни доступа', 'уд', 'статусы']:
        info_access_level(vk_user)
        return 'ok'

    command = re.search(r'пользоват\w+ (\w+)', l_text)
    if command is None:
        command = re.search(r'user\w+ (\w+)', l_text)
    if command is not None:
        user_list(vk_user=vk_user, category=command.group(1))
        return 'ok'

    if l_text in ['stn', 'круковская', 'крука']:
        stn_groups(vk_user)
        return 'ok'
    if l_text in ['прак', 'аналит', 'аналитика']:
        analytics_group(vk_user)
        return 'ok'

    error_message(vk_user.vk_id, 'Команда не распознана. Для вывода справки напишите "Справка".')
    return 'ok'

def request_processing(data):
    type = data.get('type')
    if type == None:
        logging.error('Notification with no type stated.')
        return 'Type is not defined error'
    elif type == 'confirmation':
        return verification(data)
    elif type == 'message_new':
        return new_message(data)
    else:
        logging.error('Message with unknown type.')
        return 'Unrecognized message type error'

def change_status(caller, subj_id, status):
    if not validate_vk_user(caller):
        return 'Caller validation error'
    subject = VKUser.get(vk_id=subj_id)
    if subject is None:
        error_message(caller.vk_id, 'Пользователь {} не зарегистрирован.'.format(subj_id))
        return 'User not signed up error'
    if subject.status == STATUS_ADMIN:
        error_message(caller.vk_id, 'Изменять статус администраторов возможно только через сервер.')
        return 'User is admin error'

    if status.lower() in ['u', 'unknown', 'unk', 'неопр', 'неизвестный']:
        subject.set_status(STATUS_UNKNOWN)
    elif status.lower() in ['m', 'moderator', 'moder', 'модер', 'модератор']:
        subject.set_status(STATUS_MODERATOR)
    elif status.lower() in ['a', 'admin', 'administrator', 'админ', 'администратор']:
        subject.set_status(STATUS_ADMIN)
    else:
        error_message(caller.vk_id, 'Некорректное указание кода уровня доступа.')
        return 'Invalid access key error'

    approval_message(
        caller.vk_id,
        'Пользователь @id{subj_id} ({subj_name} {subj_surname}) теперь имеет уровень доступа {status}'.format(
            subj_id = subj_id,
            subj_name = subject.name,
            subj_surnmae = subject.surname,
            status = STATUS[subject.status]
        )
    )
    notify_on_status_change(subject)

def help_message(vk_user):
    text = ('Это бот для расписаний и прочей информации. ' +
        'Пока что его функционал весьма ограничен, ' +
        'но впоследствии будет реализовано больше различных функций. ' +
        'На текущий момент Вы можете использовать следующие команды: \n' +
        '— Справка: выводит текст данной справки. \n' +
        '— STN: выводит, какие группы на этой неделе идут в какой день. \n' +
        '— Прак: выводит, какие группы на этой неделе идут на практикум по аналитике. \n' +
        '— Уровни доступа: более подробная информация о системе с уровнями доступа. \n' +
        '— Информация: (в разработке) выводит последнее информационное сообщение. \n')
    moder_level = ('Далее перечислены функции, доступные только Модераторам и Администраторам. \n' +
        '— Пользователи ВК: выводит список людей, которые писали боту и доступны для написания сообщений. \n' +
        '— Пользователи БД: выводит список людей, зарегистрированных в базе. \n')
    admin_level = ('Далее перечислены функции, доступные только Администраторам. \n' +
        '— Задать уровень доступа {login} как {access_level}.')
    if vk_user.status in ACCESS_GROUP:
        text += moder_level
    if vk_user.status == STATUS_ADMIN:
        text += admin_level
    OutgoingMessage(
        to_id=vk_user.vk_id,
        text=text
    ).send()

def info_access_level(vk_user):
    text = ('На текущий момент реализовано три уровня доступа. \n' +
        '— Администратор (A): имеет право на внесение изменений в уровень доступа других людей, ' +
        'а также обладает другими правами, доступными остальным пользователям. \n' +
        '— Модератор (M): имеет право на просмотр списка зарегистрированных пользователей и на добавление информации (в разработке). \n' +
        '— Обычный пользователь (U): не имеет прав, кроме как писать боту.')
    admin_level = ('\n\nВы являетесь администратором, '+
        'а потому можете изменять статус других людей ' +
        'при помощи команды "Задать уровень доступа {vk_id} как {status}"')
    if vk_user.status == STATUS_ADMIN:
        text += admin_level
    OutgoingMessage(
        to_id=vk_user.vk_id,
        text=text
    ).send()

def user_list(vk_user, category):
    if not validate_vk_user(vk_user):
        return 'Caller validation error'

    processed_category = ''
    if category in ['вк', 'vk', 'вконтакте']:
        processed_category = 'vk'
    elif category in ['бд', 'bd', 'база']:
        category = 'bd'
    elif category in ['все', 'оба', 'both', 'all']:
        category = 'vkbd'
    else:
        error_message(vk_user.vk_id, 'Необходимо указать категорию пользователей (БД или ВК).')
        return 'Category not stated error'
    text = ''
    if 'bd' in processed_category:
        bd_users = User.get_all()
        text += 'Пользователи базы: \n'
        for user in bd_users:
            if user.vk_user is None:
                status = 'нет связи с VKUser'
            else:
                status = STATUS[user.vk_user.status]
            text += '— @id{vk_id} ({login}): уровень доступа — {access_level}. \n'.format(
                vk_id = user.vk_id,
                login = user.login,
                access_level = status
            )
    if 'vk' in processed_category:
        vk_users = VKUser.get_all()
        text += 'Пользователи ВК: \n'
        for user in vk_users:
            text += '— @id{vk_id} ({surname} {name}): уровень доступа — {access_level}, зарегистрирован {reg_date}. \n'.format(
                vk_id = user.vk_id,
                surname = user.surname,
                name = user.name,
                access_level = STATUS[user.status],
                reg_date = user.format_reg_date()
            )
    OutgoingMessage(
        to_id = vk_user.vk_id,
        text = text
    ).send()

def unrecognized_message(vk_user):
    text = ''
    OutgoingMessage(
        to_id = vk_user.vk_id,
        text = text
    ).send()

def stn_groups(vk_user):
    text = 'На этой неделе на STN во вторник идёт группа {group_tuesday}, а в пятницу группа {group_friday}.'
    if is_week_even():
        text = text.format(group_tuesday=2, group_friday=1)
    else:
        text = text.format(group_tuesday=1, group_friday=2)

    OutgoingMessage(
        to_id = vk_user.vk_id,
        text = text
    ).send()

def analytics_group(vk_user):
    text = 'На этой неделе на аналитику идут группы {} и {}.'
    if is_week_even():
        text = text.format(2, 4)
    else:
        text = text.format(1, 3)

    OutgoingMessage(
        to_id = vk_user.vk_id,
        text = text
    ).send()
