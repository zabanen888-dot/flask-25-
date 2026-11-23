from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError


class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired(message='Введите логин')])
    password = PasswordField('Пароль', validators=[DataRequired(message='Введите пароль')])
    submit = SubmitField('Войти')


class RegisterForm(FlaskForm):
    username = StringField('Логин', validators=[
        DataRequired(message='Введите логин'),
        Length(min=3, max=30, message='Длина логина от 3 до 30 символов')
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(message='Введите пароль'),
        Length(min=8, message='Пароль должен быть не короче 8 символов')
    ])
    confirm_password = PasswordField('Повторите пароль', validators=[
        DataRequired(message='Подтвердите пароль'),
        EqualTo('password', message='Пароли не совпадают')
    ])
    submit = SubmitField('Зарегистрировать')

    def validate_password(self, field):
        password = field.data
        if not any(ch.isupper() for ch in password):
            raise ValidationError('Нужна хотя бы одна заглавная буква')
        if not any(ch.islower() for ch in password):
            raise ValidationError('Нужна хотя бы одна строчная буква')
        if not any(ch.isdigit() for ch in password):
            raise ValidationError('Нужна хотя бы одна цифра')
        if not any(ch in '!@#$%^&*()_+-=[]{}|;:,.<>?/' for ch in password):
            raise ValidationError('Нужен хотя бы один спецсимвол')
        if self.username.data and self.username.data.lower() in password.lower():
            raise ValidationError('Пароль не должен содержать логин')