from web import app
from flask import render_template, request, redirect, url_for, session
from web.service.notification_processing import request_processing
from config import ERROR_MESSAGE, VERIFICATION_RESPONSE
from web.models import VKUser, ACCESS_GROUP, User, STATUS, STATUS_MODERATOR
from web.forms import RegistrationForm, AuthForm
from web.service.helper import sign_up, cur_user


@app.route('/callback/study', methods=['POST'])
def callback():
    if not request.is_json:
        return ERROR_MESSAGE.format("Failed to read JSON")
    return request_processing(request.get_json())

@app.route('/users_list', methods=['GET', 'POST'])
def users_list():
    user = cur_user()
    if user is None or user.get_status() not in ACCESS_GROUP:
        return redirect(url_for('low_access_level', req_access=STATUS_MODERATOR))
    vk_users = VKUser.get_all()
    users = User.get_all()
    return render_template('users_list.html', user=user, title='Список пользователей', vk_users=vk_users, users=users)

@app.route('/registration', methods=['GET', 'POST'])
def registration():
    user = cur_user()
    reg_form = RegistrationForm()
    if reg_form.validate_on_submit():
        result = sign_up(
            login=reg_form.login.data,
            password=reg_form.password.data,
            vk_id=reg_form.vk_id.data
        )
        session['login'] = reg_form.login.data
        return redirect(url_for('main'))
    return render_template('registration.html', user=user, title='Регистрация',
            form=reg_form)

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    user = cur_user()
    if user is not None:
        return redirect(url_for('main'))
    auth_form = AuthForm()
    if auth_form.validate_on_submit():
        session['login'] = auth_form.login.data
        return redirect(url_for('main'))
    return render_template('auth.html', user=user, title='Вход', form=auth_form)

@app.route('/', methods=['GET'])
def main():
    user = cur_user()
    access = False
    if user is not None and user.vk_user is not None:
        access = user.get_status() in ACCESS_GROUP
    return render_template('main.html', user=user, title='Бот для расписаний', access=access)

@app.route('/deny/<string:req_access>', methods=['GET'])
def low_access_level(req_access):
    user = cur_user()
    access = STATUS[req_access]
    return render_template('low_access_level.html', user=user, req_access=access)

@app.route('/logout', methods=['GET'])
def logout():
    if 'login' in session:
        session.clear()
    return redirect(url_for('main'))
