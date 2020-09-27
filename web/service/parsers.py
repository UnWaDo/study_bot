import re


def parse_phone_number(phone_number):
    if len(phone_number) < 3:
        return None
    return re.sub(r'[\D]', '', phone_number)

def format_phone_number(phone_number):
    if len(phone_number) != 11:
        return None
    phone_list = [
        phone_number[0],
        phone_number[1:4],
        phone_number[4:7],
        phone_number[7:9],
        phone_number[9:11]
    ]
    return '+{0[0]}({0[1]}){0[2]}-{0[3]}-{0[4]}'.format(phone_list)
