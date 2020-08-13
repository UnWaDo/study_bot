from web import db
import hashlib
from config import PASSWORD_SALT
import web.service.vk_api_connector as VK

STATUS_ADMIN = 'a'
STATUS_STUDENT = 's'
STATUS_DECANATE = 'd'
STATUS_MODERATOR = 'm'
STATUS_UNKNOWN = 'u'
ACCESS_GROUP = [STATUS_ADMIN, STATUS_MODERATOR]


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    login = db.Column(db.String(32), unique=True)
    password = db.Column(db.String(128), nullable=False)
    vk_id = db.Column(db.String(8), nullable=False)
    status = db.Column(db.String(1), nullable=False)

    def __init__(self, login, vk_id, status=STATUS_UNKNOWN):
        self.login = login
        self.vk_id = vk_id
        self.status = status

    def save(self, password):
        self.password = hashlib.sha512((password+PASSWORD_SALT).encode('utf-8')).hexdigest()
        db.session.add(self)
        db.session.commit()

    def check_user(self, password):
        hash = hashlib.sha512((password+PASSWORD_SALT).encode('utf-8')).hexdigest()
        return hash == self.password

    def set_status(self, status):
        self.status = status
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get(id=None, vk_id=None, login=None):
        if login is not None:
            return User.query.filter_by(login=login).first()
        if id is not None:
            return User.query.filter_by(id=id).first()
        if vk_id is not None:
            return User.query.filter_by(vk_id=vk_id).first()
        return None

    @staticmethod
    def get_by_status(status):
        return User.query.filter_by(status=status).all()

    @staticmethod
    def get_all():
        return User.query.all()

class VKUser(db.Model):
    __tablename__ = 'vk_users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    vk_id = db.Column(db.String(8), nullable=False)
    status = db.Column(db.String(1), nullable=False)

    def __init__(self, vk_id, status=STATUS_UNKNOWN):
        self.vk_id = vk_id
        self.status = status

    def save(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get(id=None, vk_id=None):
        if vk_id is not None:
            return VKUser.query.filter_by(vk_id=vk_id).first()
        if id is not None:
            return VKUser.query.get(id)
        return None

    @staticmethod
    def get_all():
        return VKUser.query.all()

class IncomingMessage(db.Model):
    __tablename__ = 'incoming_messages'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    from_id = db.Column(db.Integer, db.ForeignKey('vk_users.id'), nullable=False)
    random_id = db.Column(db.Integer, nullable=False)
    text = db.Column(db.String(4096), nullable=False)

    def __init__(self, from_id, random_id, text):
        self.from_id = from_id
        self.random_id = random_id
        self.text = text

    def save(self):
        db.session.add(self)
        db.session.commit()

class OutgoingMessage(db.Model):
    __tablename__ = 'outgoing_messages'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    to_id = db.Column(db.Integer, db.ForeignKey('vk_users.id'), nullable=False)
    random_id = db.Column(db.Integer, nullable=False)
    text = db.Column(db.String(4096), nullable=False)

    def __init__(self, to_id, text):
        self.to_id = to_id
        self.text = text

    def send(self):
        random_id = VK.send_message(text=self.text, user_id=self.to_id)
        if random_id is None:
            return False
        self.random_id = random_id
        db.session.add(self)
        db.session.commit()
        return True
