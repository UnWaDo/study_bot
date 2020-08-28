from web.models import VKUser, User, IncomingMessage, OutgoingMessage
from web.service.helper import get_numeric_id


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

def check_registration():
    user = User.get(login='durov')
    if user is None:
        user = User(login='durov', vk_id=1)
        user.save('123456')
    print(user.check_user('123456'))
    print(user.vk_user)


check_vk_user_creation()
check_incoming_message()
check_outgoing_message()
check_registration()
