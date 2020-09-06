from wtforms import StringField, PasswordField, BooleanField, TextAreaField
from wtforms.fields.html5 import DateTimeLocalField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Length, ValidationError, StopValidation, Regexp
import web.service.vk_api_connector as VK
from web.models import User
from web.service.helper import get_numeric_id
from web.service.time_processing import to_utc, format_datetime, get_current_datetime, SITE_DATETIME_FORMAT
from datetime import datetime


def validate_vk_id(form, field):
    user = VK.get_user(field.data)
    if user is None:
        raise ValidationError('Ошибка получения информации о пользователе с таким ID.')

def validate_vk_id_is_uniq(form, field):
    vk_id = get_numeric_id(field.data)
    if User.get(vk_id=vk_id) is not None:
        raise ValidationError('Пользователь с таким ID уже зарегистрирован.')

def validate_login_is_uniq(form, field):
    user = User.get(login=field.data)
    if user is not None:
        raise ValidationError('Пользователь с таким логином уже существует.')

def check_auth_login(form, field):
    user = User.get(login=field.data)
    if user is None:
        raise StopValidation('Неизвестный логин.')

def check_auth_password(form, field):
    user = User.get(login=form.login.data)
    if user is None:
        pass
    elif not user.check_user(field.data):
        raise ValidationError('Неправильный пароль')

def check_datetime(min_dt=None, max_dt=None):
    def _check_datetime(form, field):
        if field.data is None:
            raise ValidationError('Некорректная дата')
        dt = to_utc(field.data).replace(tzinfo=None)
        if not form.need_exp_dt.data:
            return True
        if min_dt is not None and dt < min_dt:
            raise ValidationError('Дата не может быть меньше {}'.format(format_datetime(min_dt)))
        if max_dt is not None and dt > min_dt:
            raise ValidationError('Дата не может быть больше {}'.format(format_datetime(max_dt)))

    return _check_datetime

class RegistrationForm(FlaskForm):
    login = StringField('login', validators=[
        DataRequired(message='Поле "Логин" должно быть заполнено.'),
        Length(min=4, max=32, message='Длина логина должна составлять от 4 до 32 символов.'),
        Regexp(r'\w+$', message='Логин должен содержать только буквы, цифры и нижние подчёркивания.'),
        validate_login_is_uniq
    ])
    password = PasswordField('pass', validators=[
        DataRequired(message='Поле "Пароль" должно быть заполнено.'),
        Length(min=6, message='Длина пароля должна быть не менее 6 символов.')
    ])
    vk_id = StringField('vk_id', validators=[
        DataRequired(message='Поле "Идентификатор ВК" должно быть заполнено.'),
        validate_vk_id, validate_vk_id_is_uniq
    ])


class AuthForm(FlaskForm):
    login = StringField('login', validators=[DataRequired(), check_auth_login])
    password = PasswordField('password', validators=[DataRequired(), check_auth_password])

class InformationForm(FlaskForm):
    exp_dt = DateTimeLocalField('exp_dt',
        format = SITE_DATETIME_FORMAT,
        validators = [check_datetime(min_dt=datetime.utcnow())]
    )
    need_exp_dt = BooleanField('need_exp_dt', default=False)
    text = TextAreaField('text', validators=[
        Length(min=10, max=1000, message="Сообщение должно быть от 10 до 1000 символов.")
    ])
