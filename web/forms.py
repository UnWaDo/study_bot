from wtforms import StringField, PasswordField, SubmitField, SelectField
from flask_wtf import Form
from wtforms.validators import DataRequired

class RegistrationForm(Form):
    login = StringField('login', validators=[DataRequired()])
    password = PasswordField('pass', validators=[DataRequired()])
    vk_id = StringField('vk_id', validators=[DataRequired()])

class LoginForm(Form):
    login = StringField('login', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
