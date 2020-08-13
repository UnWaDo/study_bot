from web.models import User
from flask import session


def sign_up(login, password, vk_id):
    user = User(login=login, vk_id=vk_id)
    user.save(password)

def cur_user():
    if 'login' in session:
        return User.get(login=session['login'])
    return None
