from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField, \
    IntegerField, FileField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models import User

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[Required(), Length(1,64), Email()])
    password = PasswordField('Password', validators=[Required()])
    remember_me = BooleanField('Keep me logged in')
    # recaptcha = RecaptchaField()
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    name = StringField('Nama Lengkap', validators=[Required(), Length(1, 64)])
    storename = StringField('Nama Toko', validators=[Required(), Length(1, 64)])
    username = StringField('Username', validators=[
        Required(), Length(1, 64), Regexp('^[A-Za-z0-9_.]*$', 0,
                                        'Usernames must have only letters,'
                                        'numbers, dots or underscores')])
    email = StringField('E-mail', validators=[Required(), Length(1,64), Email()])
    password = PasswordField('Password', validators=[
        Required(), EqualTo('password2', message='Password must match.')])
    password2 = PasswordField('Konformasi password', validators=[Required()])
    submit = SubmitField('Daftar')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Old password', validators=[Required()])
    password = PasswordField('New password', validators=[
        Required(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Confirm new password', validators=[Required()])
    submit = SubmitField('Update Password')

class PasswordResetRequestForm(FlaskForm):
    email = StringField('Email/Username', validators=[Required(), Length(1, 64), Email()])
    submit = SubmitField('Reset Password')

class PasswordResetForm(FlaskForm):
    email = StringField('Email', validators=[Required(), Length(1, 64),
                                             Email()])
    password = PasswordField('New Password', validators=[
        Required(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Confirm password', validators=[Required()])
    submit = SubmitField('Reset Password')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError('Unknown email address.')

class EmailForm(FlaskForm):
    email = StringField('Email', validators=[Required(), Length(1, 64),
                                             Email()])
    subject = StringField('Subject :')
    body = TextAreaField('Body :')
    submit = SubmitField('Send')
