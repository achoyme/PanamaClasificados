import re
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from app.models.user import User
from app import db
from datetime import datetime
from app.utils.decorators import rate_limit

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

def sanitize_input(text):
    if not text: return ''
    return re.sub(r'<[^>]*>', '', str(text).strip())[:255]

@auth_bp.route('/login', methods=['GET', 'POST'])
@rate_limit(limit=5, per_seconds=300)
def login():
    if request.method == 'POST':
        email = sanitize_input(request.form.get('email', '')).lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            if user.is_banned:
                flash('Tu cuenta ha sido suspendida.', 'error')
                return redirect(url_for('auth.login'))
                
            login_user(user, remember=remember)
            user.last_login_at = datetime.utcnow()
            db.session.commit()
            
            flash('¡Inicio de sesión exitoso!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('main.index'))
        else:
            flash('Correo o contraseña incorrectos.', 'error')

    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
@rate_limit(limit=5, per_seconds=3600)
def register():
    if request.method == 'POST':
        first_name = sanitize_input(request.form.get('first_name', ''))
        last_name = sanitize_input(request.form.get('last_name', ''))
        email = sanitize_input(request.form.get('email', '')).lower()
        password = request.form.get('password', '')

        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            flash('Formato de correo electrónico inválido.', 'error')
            return redirect(url_for('auth.register'))

        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.', 'error')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(email=email).first():
            flash('El correo electrónico ya está registrado.', 'error')
            return redirect(url_for('auth.register'))

        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=email
        )
        new_user.set_password(password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('¡Registro exitoso! Por favor, inicia sesión.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('Ocurrió un error al registrar el usuario.', 'error')

    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('main.index'))
