from config import GROUP_ID, VERIFICATION_RESPONSE, ACCESS_TOKEN, API_VERSION
import logging, requests
from datetime import datetime, date
from random import randint
import web.service.vk_api_connector as VK
from web.models import User, VKUser, IncomingMessage, OutgoingMessage, Information
from web.models import STATUS_ADMIN, STATUS_MODERATOR, STATUS_UNKNOWN, STATUS, ACCESS_GROUP
from web.service.messager import new_user_greeting, notify_on_status_change, approval_message, error_message
from web.service.helper import validate_vk_user, get_numeric_id
from web.service.time_processing import is_week_even
import re


def verification(data):
    if str(data.get('group_id')) == GROUP_ID:
        logging.info('Group %s was confirmed.', GROUP_ID)
        return VERIFICATION_RESPONSE
    logging.error('Confirmation failed. Expected %s, found %s', GROUP_ID, data.get('group_id'))
    return 'confirmation failed'

def on_new_message(data):
    inc_message = IncomingMessage()
    inc_message.save(data['object']['message'])

    l_text = inc_message.get_text().lower()
    vk_user = inc_message.vk_user

    for command in COMMANDS.keys():
        if l_text.startswith(command):
            COMMANDS[command](vk_user, inc_message)
            return 'ok'
    print(l_text)
    error_message(vk_user.vk_id, 'Команда не распознана. Для вывода справки напишите "Справка"')
    return 'ok'

def request_processing(data):
    type = data.get('type')
    if type == None:
        logging.error('Notification with no type stated.')
        return 'Type is not defined error'
    elif type == 'confirmation':
        return verification(data)
    elif type == 'message_new':
        return on_new_message(data)
    else:
        logging.error('Message with unknown type.')
        return 'Unrecognized message type error'

def change_status(vk_user, inc_message):
    if not validate_vk_user(vk_user):
        return 'Caller validation error'

    command = re.search(r'изменить статус (\w+) на (\w+)', inc_message.get_text().lower())
    if command is None:
        error_message(vk_user.vk_id, 'Некорректный формат команды. Необходимо указать id пользователя ВКонтакте и новый статус')
        return 'Invalid input format error'

    subject = VKUser.get(vk_id=get_numeric_id(command.group(1)))
    if subject is None:
        error_message(vk_user.vk_id, 'Пользователь {} не зарегистрирован'.format(command.group(1)))
        return 'User not signed up error'
    if subject.status == STATUS_ADMIN:
        error_message(vk_user.vk_id, 'Изменять статус администраторов возможно только через сервер')
        return 'User is admin error'
    status = command.group(2).lower()
    if status == STATUS_ADMIN and vk_user.status != STATUS_ADMIN:
        error_message(vk_user.vk_id, 'Некорректное указание статуса. Возможные варианты — u, m, a')
        return 'User is not admin error'
    if status not in [STATUS_ADMIN, STATUS_MODERATOR, STATUS_UNKNOWN]:
        error_message(vk_user.vk_id, 'Некорректное указание статуса. Возможные варианты — u, m, a')
        return 'Invalid status'
    subject.set_status(status)

    approval_message(
        vk_user.vk_id,
        'Пользователь @id{subj_id} ({subj_name} {subj_surname}) теперь имеет уровень доступа {status}'.format(
            subj_id = subject.vk_id,
            subj_name = subject.name,
            subj_surname = subject.surname,
            status = subject.format_status()
        )
    )
    notify_on_status_change(subject)

def help_message(vk_user, inc_message):
    text = ('Это бот для расписаний и прочей информации. ' +
        'На текущий момент Вы можете использовать следующие команды: \n\n' +
        '— Справка: выводит текст данной справки \n\n' +
        '— STN [year-month-day]: выводит, какие группы на этой неделе идут в какой день. \n' +
        'Если указана дата, выводит то, какие группы идут в какой день на неделе, к которой относится дата \n\n' +
        '— Прак [year-month-day]: выводит, какие группы на этой неделе идут на практикум по аналитике \n' +
        'Если указана дата, выводит то, какие группы идут на неделе, к которой относится дата \n\n' +
        '— Уровни доступа: более подробная информация о системе с уровнями доступа \n\n' +
        '— Информация [истекшее] [от year-month-day]: выводит актуальные информационные сообщения \n' +
        'Если указан параметр "истекшее", то выводит в том числе и информацию с истёкшим сроком \n' +
        'Если указана дата, то выводит информацию, добавленную не ранее этой даты \n\n')
    moder_level = ('Далее перечислены функции, доступные только Модераторам и Администраторам \n\n' +
        '— Пользователи ВК: выводит список людей, которые писали боту и доступны для написания сообщений \n\n' +
        '— Пользователи БД: выводит список людей, зарегистрированных в базе \n\n')
    admin_level = ('Далее перечислены функции, доступные только Администраторам \n\n' +
        '— Изменить статус {login} на {access_level}')
    if vk_user.status in ACCESS_GROUP:
        text += moder_level
    if vk_user.status == STATUS_ADMIN:
        text += admin_level
    OutgoingMessage(
        to_id=vk_user.vk_id,
        text=text
    ).send()

def info_access_level(vk_user, inc_message):
    text = ('На текущий момент реализовано три уровня доступа \n' +
        '— Администратор (A): имеет право на внесение изменений в уровень доступа других людей, ' +
        'а также обладает другими правами, доступными остальным пользователям. \n' +
        '— Модератор (M): имеет право на просмотр списка зарегистрированных пользователей и на добавление информации \n' +
        '— Обычный пользователь (U): не имеет прав, кроме как писать боту')
    admin_level = ('\n\nВы являетесь администратором, '+
        'а потому можете изменять статус других людей ' +
        'при помощи команды "Задать уровень доступа {vk_id} как {status}"')
    self_status = '\n\nВаш статус — {}'
    if vk_user.status == STATUS_ADMIN:
        text += admin_level
    else:
        text += self_status.format(vk_user.format_status())
    OutgoingMessage(
        to_id=vk_user.vk_id,
        text=text
    ).send()

def user_list(vk_user, inc_message):
    if not validate_vk_user(vk_user):
        return 'Caller validation error'

    command = re.search(r'пользователи (\w+)', inc_message.get_text().lower())
    if command is None:
        error_message(vk_user.vk_id, 'Необходимо указать категорию пользователей (БД, ВК или все)')
        return 'Category not stated error'

    category = command.group(1)
    text = ''
    if category == 'бд' or category == 'все':
        bd_users = User.get_all()
        text += 'Пользователи базы: \n'
        for user in bd_users:
            if user.vk_user is None:
                status = 'нет связи с VKUser'
            else:
                status = user.vk_user.format_status()
            text += '— @id{vk_id} ({login}): уровень доступа — {access_level} \n'.format(
                vk_id = user.vk_id,
                login = user.login,
                access_level = status
            )
    if category == 'вк' or category == 'все':
        vk_users = VKUser.get_all()
        text += 'Пользователи ВК: \n'
        for user in vk_users:
            text += '— @id{vk_id} ({surname} {name}): уровень доступа — {access_level}, зарегистрирован {reg_date} \n'.format(
                vk_id = user.vk_id,
                surname = user.surname,
                name = user.name,
                access_level = user.format_status(),
                reg_date = user.format_reg_date()
            )
    if text == '':
        text = 'На текущий момент соответствующих пользователей нет'
    OutgoingMessage(
        to_id = vk_user.vk_id,
        text = text
    ).send()

def stn_groups(vk_user, inc_message):
    command = re.search(r'stn (\d{4})-(\d{2})-(\d{2})', inc_message.get_text().lower())
    if command is None:
        text = 'На этой неделе на STN во вторник идёт группа {group_tuesday}, а в пятницу группа {group_friday}'
        if is_week_even():
            text = text.format(group_tuesday=2, group_friday=1)
        else:
            text = text.format(group_tuesday=1, group_friday=2)
    else:
        dt = date(
            year = int(command.group(1)),
            month = int(command.group(2)),
            day = int(command.group(3))
        )
        text = 'На неделе, соответствующей {dt}, на STN во вторник идёт группа {group_tuesday}, а в пятницу группа {group_friday}'
        if is_week_even(dt):
            text = text.format(dt=dt, group_tuesday=2, group_friday=1)
        else:
            text = text.format(dt=dt, group_tuesday=1, group_friday=2)

    OutgoingMessage(
        to_id = vk_user.vk_id,
        text = text
    ).send()

def analytics_group(vk_user, inc_message):
    command = re.search(r'прак (\d{4})-(\d{2})-(\d{2})', inc_message.get_text().lower())
    if command is None:
        text = 'На этой неделе на аналитику идут группы {} и {}'
        if is_week_even():
            text = text.format(2, 4)
        else:
            text = text.format(1, 3)
    else:
        dt = date(
            year = int(command.group(1)),
            month = int(command.group(2)),
            day = int(command.group(3))
        )
        text = 'На неделе, соответствующей {}, на аналитику идут группы {} и {}'
        if is_week_even(dt):
            text = text.format(dt, group_tuesday=2, group_friday=1)
        else:
            text = text.format(dt, group_tuesday=1, group_friday=2)

    OutgoingMessage(
        to_id = vk_user.vk_id,
        text = text
    ).send()

def information_message(vk_user, inc_message):
    l_text = inc_message.get_text().lower()
    filter_expired = True
    since = None

    command = re.search(r'от (\d{4})-(\d{2})-(\d{2})', l_text)
    if command is not None:
        since = date(
            year = int(command.group(1)),
            month = int(command.group(2)),
            day = int(command.group(3))
        )
    if 'истекшее' in l_text:
        filter_expired = False

    if filter_expired:
        info_list = Information.get_unexpired(since=since)
    else:
        info_list = Information.get_all(since=since)

    if len(info_list) == 0:
        OutgoingMessage(
            to_id = vk_user.vk_id,
            text = 'Нет информации, подходящей под критерии'
        ).send()

    for info in info_list:
        OutgoingMessage(
            to_id = vk_user.vk_id,
            text = info.formatted_output()
        ).send()


COMMANDS = {
    'справка': help_message,
    'stn': stn_groups,
    'прак': analytics_group,
    'уровни доступа': info_access_level,
    'информация': information_message,
    'пользователи': user_list,
    'изменить статус': change_status
}
