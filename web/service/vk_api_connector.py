from random import randint
from config import ACCESS_TOKEN, API_VERSION, ERROR_MESSAGE
import logging, requests


MIN_SEED = -2147483648
MAX_SEED = 2147483647
TEMPLATE = ('https://api.vk.com/method/{method}?' +
            '&access_token=' + ACCESS_TOKEN +
            '&v=' + API_VERSION)


def send_message(text, user_id):
    seed = randint(MIN_SEED, MAX_SEED)
    inner_template = TEMPLATE.format(method='messages.send')

    result = requests.post(inner_template, data={
        'random_id': seed,
        'user_id': user_id,
        'message': text
    }).json()

    if result.get('error') is not None:
        logging.error('Failed to send message to user: {}'.format(result))
        return None
    else:
        return seed

def get_user(user_id, fields=None):
    inner_template = TEMPLATE.format(method='users.get')

    result = requests.post(inner_template, data={
        'user_ids': user_id,
        'fields': fields
    }).json()

    if result.get('error') is not None:
        logging.error('Failed to get user: {}'.format(result))
        return None
    else:
        return result['response'][0]
