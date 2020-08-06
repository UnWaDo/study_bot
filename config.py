from os import environ
from dotenv import load_dotenv

load_dotenv()
CSRF_ENABLED = True
SECRET_KEY = environ['SECRET_KEY']
ERROR_MESSAGE = 'error: {}'
GROUP_ID = environ['GROUP_ID']
VERIFICATION_RESPONSE = environ['VERIFICATION_RESPONSE']
