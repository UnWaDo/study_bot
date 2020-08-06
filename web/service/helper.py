from config import GROUP_ID, VERIFICATION_RESPONSE
import logging
from datetime import datetime


def verification(data):
    if str(data.get('group_id')) == GROUP_ID:
        logging.info('Group %s was confirmed.', GROUP_ID)
        return VERIFICATION_RESPONSE
    logging.error('Confirmation failed. Expected %s, found %s', GROUP_ID, data.get('group_id'))
    return 'confirmation failed'

def request_processing(data):
    type = data.get('type')
    if type == None:
        return 'type is not defined'
    elif type == 'confirmation':
        return verification(data)
    elif type == 'message_new':
        return 'ok'
    else:
        return 'unrecognized message'
