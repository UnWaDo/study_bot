from wtforms import StringField, PasswordField, BooleanField, TextAreaField, SelectField, IntegerField
from wtforms.fields.html5 import DateTimeLocalField, TimeField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Length, ValidationError, StopValidation, Regexp, Optional
import web.service.vk_api_connector as VK
from web.models import User
from web.service.helper import get_numeric_id, remove_duplicate
from web.service.time_processing import to_utc, format_datetime, get_current_datetime, SITE_DATETIME_FORMAT, WEEK_DAYS, TIME_FORMAT
from web.models import StudyGroup, EducationalOrganization, Subject, Classroom
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

def check_end_time(form, field):
    if form.end_time.data <= form.start_time.data:
        raise ValidationError('Время окончания должно быть больше времени начала')


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

class StudentsFilterForm(FlaskForm):
    id = IntegerField('person_id', validators=[Optional()])
    full_name = StringField('full_name')
    edu_org = SelectField('edu_org', validate_choice=False, coerce=int)
    department = SelectField('department', validate_choice=False, coerce=int)
    group = SelectField('group', validate_choice=False, coerce=int)

    def __init__(self, *args, **kwargs):
        super(StudentsFilterForm, self).__init__(*args, **kwargs)
        self.edu_org.choices = [(0, '')] + [(e.id, e.name) for e in sorted(EducationalOrganization.get_all(), key=lambda e: e.name)]
        self.group.choices = [(0, '')] + [(g.id, g.format_name()) for g in sorted(StudyGroup.get_all(), key=lambda g: g.format_name())]

class TeachersFilterForm(FlaskForm):
    id = IntegerField('person_id', validators=[Optional()])
    full_name = StringField('full_name')
    edu_org = SelectField('edu_org', validate_choice=False, coerce=int)
    department = SelectField('department', validate_choice=False, coerce=int)
    subject = SelectField('subject', validate_choice=False, coerce=int)

    def __init__(self, *args, **kwargs):
        super(TeachersFilterForm, self).__init__(*args, **kwargs)
        self.edu_org.choices = [(0, '')] + [(e.id, e.name) for e in sorted(EducationalOrganization.get_all(), key=lambda e: e.name)]
        subjects = [(s.id, s.name) for s in sorted(Subject.get_all(), key=lambda s: s.name)]
        subjects = remove_duplicate(subjects, key=lambda x: x[1])
        self.subject.choices = [(0, '')] + subjects

class PersonsFilterForm(FlaskForm):
    id = IntegerField('person_id', validators=[Optional()])
    full_name = StringField('full_name')
    is_student = BooleanField('is_student', default=False)
    is_teacher = BooleanField('is_teacher', default=False)

class LessonAddForm(FlaskForm):
    edu_org = SelectField('edu_org', validate_choice=False, coerce=int)
    department = SelectField('department', validate_choice=False, coerce=int)
    group = SelectField('group', validate_choice=False, coerce=int)
    subject = SelectField('subject', validate_choice=False, coerce=int)
    week_day = SelectField('week_day', choices=[(i, WEEK_DAYS[i].capitalize()) for i in range(len(WEEK_DAYS))], coerce=int)
    start_time = TimeField('start_time', format=TIME_FORMAT)
    end_time = TimeField('end_time', format=TIME_FORMAT, validators=[check_end_time])
    on_even_weeks = SelectField('on_even_weeks', choices=[(0, 'Еженедельно'), (1, 'Чётные недели'), (2, 'Нечётные недели')], default=0, coerce=int)
    classroom_edu_org = SelectField('classroom_edu_org', validate_choice=False, coerce=int)
    classroom = SelectField('classroom', validate_choice=False, coerce=int)

    def __init__(self, *args, **kwargs):
        super(LessonAddForm, self).__init__(*args, **kwargs)
        edu_orgs = [(e.id, e.name) for e in sorted(EducationalOrganization.get_all(), key=lambda e: e.name)]
        self.edu_org.choices = [(0, '')] + edu_orgs
        self.classroom_edu_org.choices = [(0, '')] + edu_orgs
        self.group.choices = [(0, '')] + [(g.id, g.format_name()) for g in sorted(StudyGroup.get_all(), key=lambda g: g.format_name())]
        subjects = [(s.id, s.name + ' — ' + s.teacher.pd.short_name()) for s in sorted(Subject.get_all(), key=lambda s: s.name)]
        self.subject.choices = [(0, '')] + subjects
        self.classrooms = [(c.id, c.edu_org.short_name + ' — ' + c.get_name()) for c in Classroom.get_all()]
