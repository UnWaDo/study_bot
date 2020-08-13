from web.models import User, OutgoingMessage, STATUS_ADMIN
from flask import session
import web.service.vk_api_connector as VK


def sign_up(login, password, vk_id):
    vk_id = get_numeric_id(vk_id)
    user = User(login=login, vk_id=vk_id)
    user.save(password)
    admin = User.get_by_status(STATUS_ADMIN)[0]
    message = OutgoingMessage(
        to_id=admin.vk_id,
        text='Новый пользователь @id{vk_id} ({login}) зарегистрировался на сайте. \
            Чтобы изменить его уровень доступа, отправьте сообщение \
            "Задать уровень доступа *login* как *уровень доступа*."'.format(
                vk_id=vk_id,
                login=login
            )
    )
    message.send()


def cur_user():
    if 'login' in session:
        return User.get(login=session['login'])
    return None

def get_numeric_id(vk_id):
    try:
        int(vk_id)
    except ValueError:
        vk_user = VK.get_user(vk_id)
        if vk_user is not None:
            vk_id = vk_user['id']
    return vk_id
