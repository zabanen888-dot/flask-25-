import json
import os
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from forms import LoginForm, RegisterForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'k9f2m8x4p1q7v3z6w5n0'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, 'users.json')


def init_storage():
    if not os.path.exists(USERS_FILE) or os.path.getsize(USERS_FILE) == 0:
        default_users = {
            'admin': {
                'password': generate_password_hash('Admin123!'),
                'registered_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'last_login': None
            }
        }
        save_users(default_users)


def load_users():
    init_storage()
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=4)


@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('register'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('register'))

    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data
        users = load_users()

        if username in users and check_password_hash(users[username]['password'], password):
            users[username]['last_login'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            save_users(users)
            session['user'] = username
            return redirect(url_for('register'))

        flash('Неверный логин или пароль', 'error')

    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user' not in session:
        return redirect(url_for('login'))

    form = RegisterForm()
    users = load_users()

    if form.validate_on_submit():
        username = form.username.data.strip()
        if any(u.lower() == username.lower() for u in users):
            flash('Пользователь с таким логином уже существует', 'error')
        else:
            users[username] = {
                'password': generate_password_hash(form.password.data),
                'registered_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'last_login': None
            }
            save_users(users)
            flash(f'Пользователь {username} создан', 'success')
            return redirect(url_for('register'))

    return render_template('register.html', form=form, users=users, current_user=session['user'])


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    init_storage()
    app.run(debug=True)