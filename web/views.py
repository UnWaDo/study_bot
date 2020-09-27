from web import app
from flask import render_template, request, redirect, url_for, session, jsonify
from web.service.notification_processing import request_processing
from config import ERROR_MESSAGE, VERIFICATION_RESPONSE
from web.models import VKUser, ACCESS_GROUP, User, Information
from web.models import STATUS, STATUS_MODERATOR, STATUS_UNREGISTERED
from web.models import Person, Teacher, Student, EducationalOrganization, Department, StudyGroup, Subject, Classroom, Lesson
from web.forms import RegistrationForm, AuthForm, InformationForm
from web.forms import StudentsFilterForm, TeachersFilterForm, PersonsFilterForm, LessonAddForm
from web.service.helper import sign_up, cur_user, remove_duplicate
from web.service.time_processing import get_current_datetime, to_utc, parse_and_transform
from web.service.time_processing import SITE_DATETIME_FORMAT
from datetime import datetime
import re


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

@app.route('/vk_user/<int:vk_id>')
def user_page(vk_id):
    user = cur_user()
    if user is None or user.get_status() == STATUS_UNREGISTERED:
        return redirect(url_for('low_access_level', req_access='m'))
    if user.vk_id != vk_id and user.get_status() not in ACCESS_GROUP:
        return redirect(url_for('low_access_level', req_access='m'))
    vk_user = VKUser.get(vk_id=vk_id)
    if vk_user is None:
        return render_template('errors/404.html', title='404', user=user), 404
    return render_template('user_page.html', title='Пользователь', user=user, vk_user=vk_user, load_js=['update_pd'])

@app.route('/vk_user/<int:vk_id>/update_pd')
def update_user_pd(vk_id):
    user = cur_user()
    if user is None or user.get_status() == STATUS_UNREGISTERED:
        return 'Not allowed', 403
    if user.vk_id != vk_id and user.get_status() not in ACCESS_GROUP:
        return 'Not allowed', 403
    vk_user = VKUser.get(vk_id=vk_id)
    if vk_user is None:
        return 'No such user', 404
    vk_user.update_pd()
    return vk_user.jsonify()

@app.route('/info/list')
def info_list():
    user = cur_user()
    today = get_current_datetime(SITE_DATETIME_FORMAT)
    info_list = Information.get_unexpired()
    info_list.reverse()
    return render_template('info_list.html', title='Информация', user=user, info_list=info_list, today=today, load_js=['filter_info'])

@app.route('/info/list/filter/<string:filter>')
def update_info_list(filter):
    since = None
    incl_expire = False
    if 'e' in filter:
        incl_expire = True
        filter = filter.replace('e', '')
    s_pos = filter.find('s')
    if s_pos >= 0:
        try:
            since = parse_and_transform(filter[s_pos+1:])
        except ValueError:
            pass
    if incl_expire:
        info_list = Information.get_all(since=since)
    else:
        info_list = Information.get_unexpired(since=since)
    info_list.reverse()
    return render_template('info_list_upd.html', info_list=info_list)

@app.route('/info/create', methods=['GET', 'POST'])
def info_create():
    user = cur_user()
    today = get_current_datetime(SITE_DATETIME_FORMAT)
    saved = False

    if user is None or user.get_status() not in ACCESS_GROUP:
        return redirect(url_for('low_access_level', req_access='m'))

    info_form = InformationForm()
    if info_form.validate_on_submit():
        if info_form.need_exp_dt.data:
            info = Information(
                author_id = user.vk_user.vk_id,
                text = info_form.text.data,
                expiration_time = to_utc(info_form.exp_dt.data).replace(tzinfo=None)
            )
            info.save()
            saved = True
        else:
            info = Information(
                author_id = user.vk_user.vk_id,
                text = info_form.text.data
            )
            info.save()
            saved = True

    return render_template('info_create.html', title='Добавить информацию', user=user, form=info_form, today=today, saved=saved, load_js=['text_limit'])

@app.route('/info/expire/<string:id>')
def info_expire(id):
    user = cur_user()
    if user is None or user.get_status() not in ACCESS_GROUP:
        return 'Not allowed', 403
    Information.get(id=id).set_expiration_time()
    return 'ok'

@app.route('/study/<string:req>', methods=['GET', 'POST'])
def req_list(req):
    user = cur_user()
    if user is None or user.get_status() not in ACCESS_GROUP:
        return redirect(url_for('low_access_level', req_access='m'))

    if req == 'persons':
        filter_form = PersonsFilterForm()
        if filter_form.validate_on_submit():
            if filter_form.id.data is not None:
                persons = Person.get(id=filter_form.id.data)
                if persons is not None:
                    persons = [persons]
            else:
                persons = [p for p in Person.get_partly(filter_form.full_name.data)]
                if filter_form.is_student.data:
                    t = [p for p in persons if p.student]
                    persons = t
                if filter_form.is_teacher.data:
                    t = [p for p in persons if p.teacher]
                    persons = t
        else:
            persons = Person.get_all()

        return render_template('study/lists/persons_list.html', title='Список физ. лиц', user=user, persons=persons, form=filter_form)
    if req == 'students':
        filter_form = StudentsFilterForm()
        if filter_form.validate_on_submit():
            if filter_form.id.data is not None:
                students = Student.get(id=filter_form.id.data)
                if students is not None:
                    students = [students]
            else:
                students = [p.student for p in Person.get_partly(filter_form.full_name.data) if p.student]
                if filter_form.group.data != 0:
                    t = [s for s in students if s.group.id == filter_form.group.data]
                    students = t
                if filter_form.department.data != 0:
                    t = [s for s in students if s.group.department.id == filter_form.department.data]
                    students = t
                elif filter_form.edu_org.data != 0:
                    t = [s for s in students if s.group.department.edu_org.id == filter_form.edu_org.data]
                    students = t
        else:
            students = Student.get_all()

        return render_template('study/lists/students_list.html', title='Список обучающихся', user=user, students=students, form=filter_form, load_js=['filter_departments', 'filter_groups'])
    if req == 'teachers':
        filter_form = TeachersFilterForm()
        if filter_form.validate_on_submit():
            if filter_form.id.data is not None:
                teachers = Teacher.get(id=filter_form.id.data)
                if teachers is not None:
                    teachers = [teachers]
            else:
                teachers = [p.teacher for p in Person.get_partly(filter_form.full_name.data) if p.teacher]
                if filter_form.subject.data != 0:
                    subject_name = Subject.get(id=filter_form.subject.data).name
                    t = [teacher for teacher in teachers if len(teacher.get_subject_by_part(name=subject_name))]
                    teachers = t
                if filter_form.department.data != 0:
                    t = [teacher for teacher in teachers if teacher.department.id == filter_form.department.data]
                    teachers = t
                elif filter_form.edu_org.data != 0:
                    t = [teacher for teacher in teachers if teacher.department.edu_org.id == filter_form.edu_org.data]
                    teachers = t
        else:
            teachers = Teacher.get_all()

        return render_template('study/lists/teachers_list.html', title='Список преподавателей', user=user, teachers=teachers, form=filter_form,  load_js=['filter_departments'])
    if req == 'edu_orgs':
        edu_orgs = EducationalOrganization.get_all()
        return render_template('study/lists/edu_orgs_list.html', title='Список учреждений', user=user, edu_orgs=edu_orgs)
    if req == 'departments':
        departments = Department.get_all()
        return render_template('study/lists/departments_list.html', title='Список подразделений', user=user, departments=departments)
    return redirect(url_for('main'))

@app.route('/study/get_departments/<int:edu_org_id>')
def get_departments(edu_org_id):
    edu_org = EducationalOrganization.get(id=edu_org_id)
    return jsonify({d.id: d.name for d in edu_org.departments})

@app.route('/study/get_groups/<int:department_id>')
def get_groups(department_id):
    department = Department.get(id=department_id)
    return jsonify({g.id: g.format_name() for g in department.groups})

@app.route('/study/get_classrooms/<int:edu_org_id>')
def get_classrooms(edu_org_id):
    edu_org = EducationalOrganization.get(id=edu_org_id)
    return jsonify({c.id: c.get_name() for c in edu_org.classrooms})

@app.route('/study/<string:req>/add', methods=['GET', 'POST'])
def req_add(req):
    user = cur_user()
    if user is None or user.get_status() not in ACCESS_GROUP:
        return redirect(url_for('low_access_level', req_access='m'))
    if req == 'lesson':
        groups = StudyGroup.get_all()
        add_form = LessonAddForm()
        if add_form.validate_on_submit():
            group = StudyGroup.get(id=add_form.group.data)
            classroom = Classroom.get(id=add_form.classroom.data)
            subject = Subject.get(id=add_form.subject.data)
            week_day = add_form.week_day.data
            if add_form.on_even_weeks.data == 1:
                on_even_week = 'e'
            elif add_form.on_even_weeks.data == 2:
                on_even_week = 'o'
            else:
                on_even_week = 'u'
            lesson = Lesson(
                group_id = group.id,
                subject_id = subject.id,
                classroom_id = classroom.id,
                start_time = add_form.start_time.data,
                end_time = add_form.end_time.data,
                week_day = week_day,
                on_even_week = on_even_week
            )
            lesson.save()
        return render_template('study/add/lesson_add.html', title='Редактировать расписание', user=user, groups=groups, form=add_form, load_js=['filter_departments', 'filter_groups', 'filter_classrooms'])

@app.route('/logout', methods=['GET'])
def logout():
    if 'login' in session:
        session.clear()
    return redirect(url_for('main'))
