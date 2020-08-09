from web import app
from flask import render_template, request
from web.service.helper import request_processing
from config import ERROR_MESSAGE, VERIFICATION_RESPONSE


@app.route('/callback/study', methods=['POST'])
def callback():
    if not request.is_json:
        return ERROR_MESSAGE.format("Failed to read JSON")
    return request_processing(request.get_json())

@app.route('/moderate', methods=['GET', 'POST'])
def moderate():
    return render_template('main.html', title='Модерация')
