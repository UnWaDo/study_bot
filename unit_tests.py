from web.models import VKUser, User, IncomingMessage, OutgoingMessage, Information
from web.service.helper import get_numeric_id
from datetime import datetime, timedelta


def check_incoming_message():
    message = {
        "date": 1596732499,
        "from_id": 98626188,
        "id": 10,
        "out": 0,
        "peer_id": 98626188,
        "text": "Ку",
        "conversation_message_id": 1,
        "fwd_messages": [],
        "important": False,
        "random_id": 0,
        "attachments": [],
        "is_hidden": False
    }
    inc_message = IncomingMessage()
    inc_message.save(message)

def check_outgoing_message():
    out_message = OutgoingMessage(98626188, 'Привет, unwado!')
    print(out_message.send())

def check_vk_user_creation():
    id = get_numeric_id('unwado')
    vk_user = VKUser.get(vk_id=id)
    if vk_user is None:
        vk_user = VKUser(
            vk_id = id,
            status = 'a'
        )
        vk_user.save()
    print(vk_user.jsonify())
    vk_user.update_pd()
    print(vk_user.jsonify())

def check_registration():
    user = User.get(login='durov')
    if user is None:
        user = User(login='durov', vk_id=1)
        user.save('123456')
    print(user.check_user('123456'))
    print(user.vk_user)

def check_information():
    author = User.get(login='unwado').vk_user

    unexp_inf = Information(
        author_id = author.vk_id,
        text = 'This is the most valuable information in the world.'
    )
    unexp_inf.save()
    exp_inf = Information(
        author_id = author.vk_id,
        text = 'This is the most valuable information in the world for now.',
        expiration_time = datetime.utcnow() + timedelta(0, 0, 2)
    )
    exp_inf.save()

def check_information_expiration():
    all_information = Information.get_all()
    unexp = Information.get_unexpired()

    for i in all_information:
        print('Creation date: {} \nText: {}\nExpired: {}'.format(i.creation_time, i.text, i.was_expired()))
    print('\n\nUnexpired:')
    for i in unexp:
        print('Creation date: {} \nText: {}'.format(i.creation_time, i.text))
