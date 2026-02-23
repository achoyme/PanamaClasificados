from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from app.models import User
from app import db
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET': return render_template('auth/register.html')
    user = User(email=request.form.get('email'), first_name=request.form.get('first_name'), last_name=request.form.get('last_name'), phone_number=request.form.get('phone_number'))
    user.set_password(request.form.get('password'))
    db.session.add(user)
    db.session.commit()
    flash('Cuenta creada. Inicia sesión.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET': return render_template('auth/login.html')
    user = User.query.filter_by(email=request.form.get('email')).first()
    if user and user.check_password(request.form.get('password')):
        login_user(user, remember=request.form.get('remember'))
        return redirect(url_for('main.index'))
    flash('Credenciales incorrectas', 'error')
    return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))