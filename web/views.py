from web import app
from flask import render_template, request, redirect, url_for, session
from web.service.notification_processing import request_processing
from config import ERROR_MESSAGE, VERIFICATION_RESPONSE
from web.models import VKUser, ACCESS_GROUP, User
from web.forms import RegistrationForm, AuthForm
from web.service.helper import sign_up, cur_user


@app.route('/callback/study', methods=['POST'])
def callback():
    if not request.is_json:
        return ERROR_MESSAGE.format("Failed to read JSON")
    return request_processing(request.get_json())

@app.route('/moderate', methods=['GET', 'POST'])
def moderate():
    user = cur_user()
    if user is None or user.status not in ACCESS_GROUP:
        return redirect(url_for('main'))
    vk_users = VKUser.get_all()
    users = User.get_all()
    return render_template('moderate.html', title='Модерация', vk_users=vk_users, users=users)

@app.route('/registration', methods=['GET', 'POST'])
def registration():
    reg_form = RegistrationForm()
    if reg_form.validate_on_submit():
        result = sign_up(
            login=reg_form.login.data,
            password=reg_form.password.data,
            vk_id=reg_form.vk_id.data
        )
    return render_template('registration.html', title='Регистрация',
            form=reg_form)

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    user = cur_user()
    if user is not None:
        return redirect(url_for('moderate'))
    auth_form = AuthForm()
    if auth_form.validate_on_submit():
        session['login'] = auth_form.login.data
        return redirect(url_for('moderate'))
    return render_template('auth.html', title='Вход', form=auth_form)

@app.route('/', methods=['GET'])
def main():
    user = cur_user()
    access = False
    if user is not None:
        access = user.status in ACCESS_GROUP
    return render_template('main.html', title='Управление', user=user, access=access)

@app.route('/logout', methods=['GET'])
def logout():
    if 'login' in session:
        session.clear()
    return redirect(url_for('main'))
