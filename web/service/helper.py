from web.models import User, STATUS_ADMIN, ACCESS_GROUP
from flask import session
import web.service.vk_api_connector as VK
from web.service.messager import notify_admin_on_registration, error_message
import re


def sign_up(login, password, vk_id):
    vk_id = get_numeric_id(vk_id)
    user = User(login=login, vk_id=vk_id)
    user.save(password)
    notify_admin_on_registration(user)

def cur_user():
    if 'login' in session:
        return User.get(login=session['login'])
    return None

def get_numeric_id(vk_id):
    try:
        int(vk_id)
    except ValueError:
        if vk_id == '':
            return None

        vk_user = VK.get_user(vk_id)
        if vk_user is None:
            return None
        else:
            vk_id = vk_user['id']
    return vk_id

def validate_vk_user(vk_user, allowed=ACCESS_GROUP):
    if vk_user.status in allowed:
        return True
    else:
        error_message(vk_user.vk_id, 'Недостаточный уровень доступа для выполнения команды.')
        return False

def validate_user(user, allowed=ACCESS_GROUP):
    if user.vk_user is None:
        return False
    if user.vk_user.status in allowed:
        return True
    else:
        return False

def remove_duplicate(d_list, key=None):
    unique = []
    if key is None:
        for el in d_list:
            if el not in unique:
                unique.append(el)
    else:
        keys = []
        for el in d_list:
            if key(el) not in keys:
                unique.append(el)
                keys.append(key(el))
    return unique
