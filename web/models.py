from web import db
import hashlib
from config import PASSWORD_SALT
import web.service.vk_api_connector as VK
from datetime import datetime, date
from web.service.time_processing import format_date, format_datetime, DATE_FORMAT, format_birth_date, format_time, WEEK_DAYS
from web.service.parsers import format_phone_number
from web.service.exceptions import *
from flask import url_for
import time


STATUS_ADMIN = 'a'
STATUS_STUDENT = 's'
STATUS_DECANATE = 'd'
STATUS_MODERATOR = 'm'
STATUS_UNREGISTERED ='r'
STATUS_UNKNOWN = 'u'
STATUS = {
    STATUS_ADMIN: 'Администратор',
    STATUS_UNKNOWN: 'Пользователь',
    STATUS_MODERATOR: 'Модератор',
    STATUS_UNREGISTERED: 'Не зарегистрирован'
}
ACCESS_GROUP = [STATUS_ADMIN, STATUS_MODERATOR]


class VKUser(db.Model):
    __tablename__ = 'vk_users'
    vk_id = db.Column('vk_id', db.Integer, primary_key=True)
    reg_date = db.Column('reg_date', db.DateTime, nullable=False)
    birth_date = db.Column('birth_date', db.DateTime)
    name = db.Column('name', db.String(40))
    surname = db.Column('surname', db.String(45))
    status = db.Column('status', db.String(1), nullable=False)

    user = db.relationship('User', backref='vk_user', uselist=False)
    inc_messages = db.relationship('IncomingMessage', backref='vk_user', uselist=True)
    outg_messages = db.relationship('OutgoingMessage', backref='vk_user', uselist=True)
    information = db.relationship('Information', backref='author', uselist=True)
    person = db.relationship('Person', backref='vk_user', uselist=False)

    def __init__(self, vk_id, status=STATUS_UNKNOWN):
        self.vk_id = int(vk_id)
        self.reg_date = datetime.utcnow()
        self.status = status.lower()

    def jsonify(self):
        json = '{'
        json += '"vk_id": {}, '.format(self.vk_id)
        json += '"reg_date": "{}", '.format(self.format_reg_date())
        json += '"status": "{}"'.format(STATUS[self.status])
        if self.surname:
            json += ', "surname": "{}"'.format(self.surname)
        if self.name:
            json += ', "name": "{}"'.format(self.name)
        if self.birth_date:
            json += ', "birth_date": "{}"'.format(self.format_birth_date())
        json += '}'
        return json

    def save(self):
        db.session.add(self)
        db.session.commit()

    def update_pd(self):
        user = VK.get_user(self.vk_id, fields='bdate')
        if user is None:
            return False
        self.name = user.get('first_name', '')
        self.surname = user.get('last_name', '')
        birth_date = user.get('bdate')
        if birth_date is None:
            pass
        elif len(birth_date) <= 5:
            self.birth_date = datetime.strptime(birth_date, '%d.%m')
        elif len(birth_date) > 5:
            self.birth_date = datetime.strptime(birth_date, '%d.%m.%Y')
        db.session.add(self)
        db.session.commit()

    def set_status(self, status):
        self.status = status.lower()
        db.session.add(self)
        db.session.commit()

    def format_reg_date(self):
        return format_date(self.reg_date)

    def format_birth_date(self):
        return format_date(self.birth_date)

    def format_status(self):
        return STATUS[self.status]

    def get_all_messages(self):
        messages = [('inc', inc.message) for inc in self.inc_messages]
        for outg in self.outg_messages:
            messages.append(('outg', outg.message))
        messages.sort(key=lambda x: x[1].datetime)
        messages.reverse()
        return messages

    @staticmethod
    def get(id=None, vk_id=None, status=None):
        if vk_id is not None:
            return VKUser.query.filter_by(vk_id=vk_id).first()
        if id is not None:
            return VKUser.query.get(id)
        if status is not None:
            return VKUser.query.filter_by(status=status).all()
        return None

    @staticmethod
    def get_all():
        return VKUser.query.all()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    login = db.Column(db.String(32), unique=True)
    password = db.Column(db.String(128), nullable=False)
    vk_id = db.Column(db.Integer, db.ForeignKey('vk_users.vk_id'), nullable=False)

    def __init__(self, login, vk_id):
        self.login = login.lower()
        self.vk_id = int(vk_id)

    def save(self, password):
        self.password = hashlib.sha512((password+PASSWORD_SALT).encode('utf-8')).hexdigest()
        db.session.add(self)
        db.session.commit()

    def check_user(self, password):
        hash = hashlib.sha512((password+PASSWORD_SALT).encode('utf-8')).hexdigest()
        return hash == self.password

    def get_status(self):
        if self.vk_user is None:
            return STATUS_UNREGISTERED
        else:
            return self.vk_user.status

    def format_status(self):
        return STATUS[self.get_status()]

    @staticmethod
    def get(id=None, vk_id=None, login=None, status=None):
        if login is not None:
            return User.query.filter_by(login=login.lower()).first()
        if id is not None:
            return User.query.filter_by(id=id).first()
        if vk_id is not None:
            return User.query.filter_by(vk_id=vk_id).first()
        return None

    @staticmethod
    def get_all():
        return User.query.all()

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    datetime = db.Column(db.DateTime, nullable=False)
    random_id = db.Column(db.Integer, nullable=False)
    text = db.Column(db.String(1000), nullable=False)
    long_text = db.relationship('LongText', backref='message', uselist=False)

    def save(self):
        text = self.text
        self.text = text[:1000]
        long_text = None
        db.session.add(self)
        db.session.commit()
        if len(text) > 1000:
            long = LongText(text=text, message_id=self.id)
            long.save()
            self.long_text = long
            db.session.add(self)
            db.session.commit()

    def format_datetime(self):
        return format_datetime(self.datetime)

    def get_text(self):
        if self.long_text is not None:
            return self.long_text.text
        return self.text

class LongText(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    text = db.Column(db.String(4096))
    message_id = db.Column(db.Integer, db.ForeignKey('messages.id'), nullable=False)

    def save(self):
        db.session.add(self)
        db.session.commit()

    def get_text(self):
        return self.message.get_text()

class IncomingMessage(db.Model):
    __tablename__ = 'incoming_messages'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    message_id = db.Column(db.Integer, db.ForeignKey('messages.id'), nullable=False)
    from_id = db.Column(db.Integer, db.ForeignKey('vk_users.vk_id'), nullable=False)
    message = db.relationship('Message', backref='inc_message', uselist=False)

    def save(self, message):
        send_date = datetime.strptime(
            time.ctime(message['date']),
            '%a %b %d %H:%M:%S %Y'
        )
        msg_obj = Message(
            datetime = send_date,
            random_id = message['random_id'],
            text = message['text']
        )
        msg_obj.save()

        self.message_id = msg_obj.id
        self.from_id = message['from_id']
        db.session.add(self)
        db.session.commit()

    def get_text(self):
        return self.message.get_text()

class OutgoingMessage(db.Model):
    __tablename__ = 'outgoing_messages'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    message_id = db.Column(db.Integer, db.ForeignKey('messages.id'), nullable=False)
    to_id = db.Column(db.Integer, db.ForeignKey('vk_users.vk_id'), nullable=False)
    message = db.relationship('Message', backref='out_message', uselist=False)

    def __init__(self, to_id, text):
        self.to_id = to_id
        self.text = text

    def send(self):
        random_id = VK.send_message(text=self.text, user_id=self.to_id)
        if random_id is None:
            return False
        message = Message(
            datetime = datetime.utcnow(),
            random_id = random_id,
            text = self.text
        )
        message.save()
        self.message_id = message.id
        db.session.add(self)
        db.session.commit()
        return True

class Information(db.Model):
    __tablename__ = 'information'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    creation_time = db.Column(db.DateTime, nullable=False)
    expiration_time = db.Column(db.DateTime)
    modification_time = db.Column(db.DateTime, nullable=False)
    text = db.Column(db.String(1000), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('vk_users.vk_id'), nullable=False)
    approved = db.Column(db.Boolean, nullable=False)

    def __init__(self, author_id, text, expiration_time=None):
        self.author_id = author_id
        self.text = text

        author = VKUser.get(vk_id=author_id)
        if author is None or author.status not in ACCESS_GROUP:
            self.approved = False
        else:
            self.approved = True

        self.creation_time = datetime.utcnow()
        self.modification_time = self.creation_time
        self.expiration_time = expiration_time

    def save(self):
        db.session.add(self)
        db.session.commit()

    def was_modified(self):
        if self.creation_time == self.modification_time:
            return False
        else:
            return True

    def was_expired(self, dt=None):
        if dt is None:
            dt = datetime.utcnow()
        if self.expiration_time is None or dt < self.expiration_time:
            return False
        else:
            return True

    def approve(self, vk_user):
        if vk_user.status in ACCESS_GROUP:
            self.approved = True
            db.session.add(self)
            db.session.commit()
        return self.approved

    def set_expiration_time(self, exp_time=None):
        if exp_time is None:
            exp_time = datetime.utcnow()
        self.expiration_time = exp_time
        db.session.add(self)
        db.session.commit()

    def formatted_output(self):
        text = 'Дата публикации: {} \n'.format(self.format_ct())
        if self.modification_time != self.creation_time:
            text += 'Изменено: {} \n'.format(self.format_mt())
        if self.expiration_time:
            text += 'Действительно до: {} \n'.format(self.format_et())
        text += 'by @id{} ({} {})\n'.format(self.author.vk_id, self.author.surname, self.author.name)
        text += '————————\n{}\n————————'.format(self.text)
        return text

    def format_ct(self):
        return format_datetime(self.creation_time)

    def format_mt(self):
        return format_datetime(self.modification_time)

    def format_et(self):
        return format_datetime(self.expiration_time)

    def expire_link(self):
        return url_for('info_expire', id=self.id)

    @staticmethod
    def get(id):
        return Information.query.filter_by(id=id).first()

    @staticmethod
    def get_unexpired(since=None):
        info_list = Information.query.filter_by(approved=True).all()
        if since is not None:
            info_list = list(filter(lambda info: info.creation_time >= since, info_list))

        info_list = list(filter(lambda info: not info.was_expired(), info_list))
        return info_list

    @staticmethod
    def get_all(since=None):
        info_list = Information.query.filter_by(approved=True).all()
        if since is None:
            return info_list
        info_list = list(filter(lambda info: info.creation_time >= since, info_list))
        return info_list

class EducationalOrganization(db.Model):
    __tablename__ = 'edu_orgs'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(132), nullable=False, unique=True)
    short_name = db.Column(db.String(10), nullable=False)

    departments = db.relationship('Department', backref='edu_org')
    classrooms = db.relationship('Classroom', backref='edu_org')

    def __init__(self, name, short_name):
        self.name = name
        self.short_name = short_name

    def save(self):
        db.session.add(self)
        db.session.commit()

    def get_department(self, name=None, short_name=None):
        if name is not None:
            name = name.lower()
            filtered = filter(lambda d: d.name.lower() == name, self.departments)
        elif short_name is not None:
            short_name = short_name.lower()
            filtered = filter(lambda d: d.short_name.lower() == short_name, self.departments)

        filtered = list(filtered)
        if len(filtered) > 1:
            raise DepartmentIsNotUniqueException('More than one department for a educational organization with definite name')
        elif len(filtered) == 1:
            return filtered[0]
        else:
            return None

    def get_classroom(self, name):
        name = name.lower()
        classrooms = filter(lambda c: c.get_name().lower() == name.lower(), self.classrooms)
        classrooms = list(classrooms)
        if len(classrooms) > 1:
            raise ClassroomIsNotUniqueException('More than one group for a department with definite name')
        elif len(classrooms) == 1:
            return classrooms[0]
        else:
            return None

    @staticmethod
    def get_all():
        return EducationalOrganization.query.all()

    @staticmethod
    def get(id=None, name=None, short_name=None):
        if id is not None:
            return EducationalOrganization.query.filter_by(id=id).first()
        if name is not None:
            return EducationalOrganization.query.filter_by(name=name).first()
        if short_name is not None:
            return EducationalOrganization.query.filter_by(short_name=short_name).all()
        return None

class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    edu_org_id = db.Column(db.Integer, db.ForeignKey('edu_orgs.id'), nullable=False)
    name = db.Column(db.String(75), nullable=False)
    short_name = db.Column(db.String(10), nullable=False)

    groups = db.relationship('StudyGroup', backref='department')
    teachers = db.relationship('Teacher', backref='department')

    def save(self):
        db.session.add(self)
        db.session.commit()

    def get_group_by_name(self, name):
        filtered = filter(lambda g: g.format_name() == name, self.groups)
        filtered = list(filtered)
        if len(filtered) > 1:
            raise GroupIsNotUniqueException('More than one group for a department with definite name')
        elif len(filtered) == 1:
            return filtered[0]
        else:
            return None

    @staticmethod
    def get_all():
        return Department.query.all()

    @staticmethod
    def get(id=None, name=None, short_name=None):
        if id is not None:
            return Department.query.filter_by(id=id).first()
        if name is not None:
            return Department.query.filter_by(name=name).first()
        if short_name is not None:
            return Department.query.filter_by(short_name=short_name).first()
        return None

class StudyGroup(db.Model):
    __tablename__ = 'study_groups'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    name_format = db.Column(db.String(6), nullable=False)
    elder_id = db.Column(db.Integer, db.ForeignKey('students.person_id'))
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)

    students = db.relationship('Student', foreign_keys='Student.group_id', backref='group', uselist=True)
    lessons = db.relationship('Lesson', backref='group', uselist=True)

    def save(self):
        db.session.add(self)
        db.session.commit()

    def format_name(self):
        now = date.today()
        if now < self.end_date:
            return self.name_format.replace('*', str(now.year - self.start_date.year + 1))
        else:
            return '—'

    def get_elder(self):
        if self.elder_id is None:
            return None
        return Student.get(id=self.elder_id)

    def get_lessons(self, week_day=None, is_week_even=None):
        if week_day is None and is_week_even is None:
            return sorted(self.lessons, key=lambda l: (l.week_day, l.start_time))
        else:
            lessons = self.lessons
            if week_day is not None:
                lessons = [l for l in lessons if l.week_day == week_day]
            if is_week_even is not None:
                lessons = [l for l in lessons if (l.on_even_week == 'u') or (l.on_even_week == is_week_even)]
            return sorted(lessons, key=lambda l: (l.week_day, l.start_time))

    @staticmethod
    def get_all():
        return StudyGroup.query.all()

    @staticmethod
    def get_by_name(name):
        all = StudyGroup.query.all()
        filtered = filter(lambda group: name == group.format_name(), all)
        return list(filtered)

    @staticmethod
    def get(id=None, name_format=None, department_id=None):
        if id is not None:
            return StudyGroup.query.filter_by(id=id).first()
        if name_format is not None:
            return StudyGroup.query.filter_by(name_format=name_format).first()
        if id is not None:
            return StudyGroup.query.filter_by(department_id=department_id).all()

class Person(db.Model):
    __tablename__ = 'persons'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    surname = db.Column(db.String(45), nullable=False)
    name = db.Column(db.String(40), nullable=False)
    father_name = db.Column(db.String(45))
    birth_date = db.Column(db.Date)
    vk_id = db.Column(db.Integer, db.ForeignKey('vk_users.vk_id'))
    phone_number = db.Column(db.String(11))
    email = db.Column(db.String(50))

    student = db.relationship('Student', backref='pd', uselist=False)
    teacher = db.relationship('Teacher', backref='pd', uselist=False)

    def save(self):
        db.session.add(self)
        db.session.commit()

    def full_name(self):
        if self.father_name is not None:
            return '{} {} {}'.format(self.surname, self.name, self.father_name)
        else:
            return '{} {}'.format(self.surname, self.name)

    def short_name(self):
        if self.father_name is not None:
            return '{} {}.{}.'.format(self.surname, self.name[0], self.father_name[0])
        else:
            return '{} {}.'.format(self.surname, self.name[0])

    def get_birth_date(self):
        if self.birth_date is not None:
            return format_birth_date(self.birth_date)

    def get_phone_number(self):
        if self.phone_number is not None:
            return format_phone_number(self.phone_number)

    @staticmethod
    def get_by_match(surname, name, father_name=None, birth_date=None, vk_id=None, phone_number=None, email=None):
        persons = Person.query.filter_by(
            surname = surname,
            name = name,
            father_name = father_name
        ).all()
        for p in persons:
            if p.birth_date == birth_date:
                return p
            if p.vk_id == vk_id:
                return p
            if p.phone_number == phone_number:
                return p
            if p.email == email:
                return p
        return None

    @staticmethod
    def get(id=None, surname=None, vk_id=None, phone_number=None, email=None):
        if id is not None:
            return Person.query.filter_by(id=id).first()
        if surname is not None:
            return Person.query.filter_by(surname=surname).all()
        if vk_id is not None:
            return Person.query.filter_by(vk_id=vk_id).first()
        if phone_number is not None:
            return Person.query.filter_by(phone_number=phone_number).first()
        if email is not None:
            return Person.query.filter_by(email=email).first()
        return None

    @staticmethod
    def get_all():
        return Person.query.all()

    @staticmethod
    def get_partly(string=None):
        all = Person.query.all()
        filtered = filter(lambda person: string.lower() in person.full_name().lower(), all)
        return list(filtered)

    @staticmethod
    def get_students():
        all = Person.query.all()
        filtered = filter(lambda person: person.student is not None, all)
        return list(filtered)

    @staticmethod
    def get_teachers():
        all = Person.query.all()
        filtered = filter(lambda person: person.teacher is not None, all)
        return list(filtered)

class Student(db.Model):
    __tablename__ = 'students'
    person_id = db.Column(db.Integer, db.ForeignKey('persons.id'), primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('study_groups.id', use_alter=True), nullable=False)

    def save(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_all():
        return Student.query.all()

    @staticmethod
    def get(id):
        return Student.query.filter_by(person_id=id).first()

class Teacher(db.Model):
    __tablename__ = 'teachers'
    person_id = db.Column(db.Integer, db.ForeignKey('persons.id'), primary_key=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)

    subjects = db.relationship('Subject', backref='teacher', uselist=True)

    def save(self):
        db.session.add(self)
        db.session.commit()

    def get_subject(self, name):
        name = name.lower()
        filtered = filter(lambda s: s.name.lower() == name, self.subjects)
        filtered = list(filtered)
        if len(filtered) > 1:
            raise SubjectIsNotUniqueException('More than one subject for a teacher with definite name')
        elif len(filtered) == 1:
            return filtered[0]
        else:
            return None

    def get_subject_by_part(self, name):
        name = name.lower()
        filtered = filter(lambda s: name in s.name.lower(), self.subjects)
        return list(filtered)

    @staticmethod
    def get_all():
        return Teacher.query.all()

class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(75), nullable=False)
    short_name = db.Column(db.String(10), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.person_id'), nullable=False)

    lessons = db.relationship('Lesson', backref='subject', uselist=True)

    def save(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_all():
        return Subject.query.all()

    @staticmethod
    def get(id=None, name=None):
        if id is not None:
            return Subject.query.filter_by(id=id).first()
        if name is not None:
            subjects = Subject.query.all()
            name = name.lower()
            return [s for s in subjects if name.lower() in s.name.lower()]

class Classroom(db.Model):
    __tablename__ = 'classrooms'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    edu_org_id = db.Column(db.Integer, db.ForeignKey('edu_orgs.id'), nullable=False)
    number_format = db.Column(db.String(5), nullable=False)
    number = db.Column(db.Integer)

    lessons = db.relationship('Lesson', backref='classroom', uselist=True)

    def save(self):
        db.session.add(self)
        db.session.commit()

    def get_name(self):
        return self.number_format.replace('*', str(self.number))

    @staticmethod
    def get_all():
        return Classroom.query.all()

    @staticmethod
    def get(id=None, name=None):
        if id is not None:
            return Classroom.query.filter_by(id=id).first()
        if name is not None:
            classrooms = Classroom.get_all()
            name = name.lower()
            return [c for c in classrooms if c.get_name().lower() == name]


class Lesson(db.Model):
    __tablename__ = 'lessons'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    group_id = db.Column(db.Integer, db.ForeignKey('study_groups.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classrooms.id'), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    week_day = db.Column(db.Integer, nullable=False)
    on_even_week = db.Column(db.String(1), nullable=False)

    def save(self):
        db.session.add(self)
        db.session.commit()

    def formatted_output(self):
        return '{since}—{till}: {subject}, {teacher}, {place} ({edu_org})'.format(
            since = format_time(self.start_time),
            till = format_time(self.end_time),
            subject = self.subject.name,
            teacher = self.subject.teacher.pd.short_name(),
            place = self.classroom.get_name(),
            edu_org = self.classroom.edu_org.short_name
        )

    def get_week_day(self):
        return WEEK_DAYS[self.week_day].capitalize()

    def is_on_even_week(self):
        if self.on_even_week == 'e':
            return True
        elif self.on_even_week == 'o':
            return False
        else:
            return None
