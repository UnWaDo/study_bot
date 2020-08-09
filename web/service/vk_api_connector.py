from random import randint
from config import ACCESS_TOKEN, API_VERSION, ERROR_MESSAGE
import logging, requests

MIN_SEED = -2147483648
MAX_SEED = 2147483647
TEMPLATE = 'https://api.vk.com/method/{method}?{params}'

def send_message(text, user_id):
    seed = randint(MIN_SEED, MAX_SEED)
    inner_template = TEMPLATE.format(
        method = 'messages.send',
        params = 'random_id={seed}&user_id={u_id}&access_token={token}&v={v}&message={text}'
    )

    result = requests.get(inner_template.format(
        seed = seed,
        u_id = user_id,
        token = ACCESS_TOKEN,
        v = API_VERSION,
        text = text)
    ).json()

    if result.get('error') is not None:
        print(result)
        logging.error('Failed to send message to user: {}'.format(result))
        return None
    else:
        return result.get('response')

def get_user(user_id):
    inner_template = TEMPLATE.format(
        method = 'users.get',
        params = 'user_id={u_id}&access_token={token}&v={v}'
    )

    result = requests.get(inner_template.format(
        u_id = user_id,
        token = ACCESS_TOKEN,
        v = API_VERSION)
    ).json()

    if result.get('error') is not None:
        logging.error('Failed to get user: {}'.format(result))
        return None
    else:
        return result['response'][0]
