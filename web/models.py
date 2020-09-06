from web import db
import hashlib
from config import PASSWORD_SALT
import web.service.vk_api_connector as VK
from datetime import datetime
from web.service.time_processing import format_date, format_datetime, DATE_FORMAT
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
        return self.reg_date.strftime(DATE_FORMAT)

    def format_status(self):
        return STATUS[self.status]

    def get_all_messages(self):
        messages = [('inc', inc.message) for inc in self.inc_messages]
        for outg in self.outg_messages:
            messages.append(('outg', outg.message))
        messages.sort(key=lambda x: x[1].datetime)
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


class LongText(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    text = db.Column(db.String(4096))
    message_id = db.Column(db.Integer, db.ForeignKey('messages.id'), nullable=False)

    def save(self):
        db.session.add(self)
        db.session.commit()

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

    def was_expired(self, dt=datetime.utcnow()):
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

    def set_expiration_time(self, exp_time=datetime.utcnow()):
        self.expiration_time = exp_time
        db.session.add(self)
        db.session.commit()

    def formatted_output(self):
        text = 'Дата публикации: {} \n'.format(self.format_ct())
        if self.modification_time != self.creation_time:
            text += 'Изменено: {} \n'.format(self.format_mt())
        if self.expiration_time:
            text += 'Действительно до: {} \n'.format(self.format_et())
        text += '\n{}'.format(self.text)
        text += '\nby @id{} ({} {})'.format(self.author.vk_id, self.author.surname, self.author.name)
        return text

    def format_ct(self):
        return format_datetime(self.creation_time)

    def format_mt(self):
        return format_datetime(self.modification_time)

    def format_et(self):
        return format_datetime(self.expiration_time)

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
