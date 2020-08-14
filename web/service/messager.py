import web.service.vk_api_connector as VK
from web.models import STATUS_ADMIN, STATUS_UNKNOWN, STATUS_MODERATOR, STATUS, OutgoingMessage


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


def notify_admin_on_registration(user):
    admin = User.get_by_status(STATUS_ADMIN)[0]
    OutgoingMessage(
        to_id=admin.vk_id,
        text='Новый пользователь @id{vk_id} ({login}) зарегистрировался на сайте. \
            Чтобы изменить его уровень доступа, отправьте сообщение \
            "Задать уровень доступа *login* как *уровень доступа*."'.format(
                vk_id=user.vk_id,
                login=user.login
            )
    ).send()

def notify_on_status_change(user):
    OutgoingMessage(
        to_id=user.vk_id,
        text='Ваш уровень доступа к боту изменён.\n \
            Текущий уровень доступа: {}'.format(STATUS[user.status])
    ).send()

def approval_message(vk_id, text):
    OutgoingMessage(
        to_id=vk_id,
        text='Запрошенная Вами команда выполнена успешно. \n {}'.format(text)
    ).send()

def error_message(vk_id, text):
    OutgoingMessage(
        to_id=vk_id,
        text='Ошибка при выполнении команды. \n {}'.format(text)
    ).send()