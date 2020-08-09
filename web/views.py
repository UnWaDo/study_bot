from web import app
from flask import render_template, request
from web.service.helper import request_processing
from config import ERROR_MESSAGE, VERIFICATION_RESPONSE
from web.models import VKUser


@app.route('/callback/study', methods=['POST'])
def callback():
    if not request.is_json:
        return ERROR_MESSAGE.format("Failed to read JSON")
    return request_processing(request.get_json())

@app.route('/moderate', methods=['GET', 'POST'])
def moderate():
    users = VKUser.get_all()
    return render_template('main.html', title='Модерация', users=users)
