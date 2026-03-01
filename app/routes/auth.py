import re
import secrets
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app import db
from datetime import datetime, timedelta
from app.utils.decorators import rate_limit
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Serializador para tokens seguros
serializer = URLSafeTimedSerializer('dev-secret-key')

def sanitize_input(text):
    if not text: return ''
    return re.sub(r'<[^>]*>', '', str(text).strip())[:255]

def validate_password_strength(password):
    """🔐 Valida fortaleza de contraseña"""
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres."
    if not re.search(r'[A-Z]', password):
        return False, "La contraseña debe incluir al menos una mayúscula."
    if not re.search(r'[a-z]', password):
        return False, "La contraseña debe incluir al menos una minúscula."
    if not re.search(r'\d', password):
        return False, "La contraseña debe incluir al menos un número."
    return True, "Contraseña válida"

def generate_reset_token(email):
    """Genera token seguro con expiración de 1 hora"""
    return serializer.dumps(email, salt='password-reset-salt')

def verify_reset_token(token, expiration=3600):
    """Verifica token y retorna email si es válido"""
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=expiration)
        return email
    except SignatureExpired:
        return None
    except BadSignature:
        return None

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
                flash('Tu cuenta ha sido suspendida. Contacta soporte.', 'error')
                return redirect(url_for('auth.login'))
            
            login_user(user, remember=remember)
            user.last_login_at = datetime.utcnow()
            
            # ✅ NUEVO: Rastrear la IP para el sistema Anti-Fraude
            user.last_ip_address = request.remote_addr
            
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
        
        is_valid, message = validate_password_strength(password)
        if not is_valid:
            flash(message, 'error')
            return redirect(url_for('auth.register'))
        
        if User.query.filter_by(email=email).first():
            flash('El correo electrónico ya está registrado.', 'error')
            return redirect(url_for('auth.register'))
        
        # ✅ NUEVO: Guardar IP al registrarse
        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            last_ip_address=request.remote_addr
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

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
@rate_limit(limit=3, per_seconds=3600)
def forgot_password():
    """📧 Solicitar recuperación de contraseña"""
    if request.method == 'POST':
        email = sanitize_input(request.form.get('email', '')).lower()
        user = User.query.filter_by(email=email).first()
        
        if user:
            token = generate_reset_token(user.email)
            reset_link = url_for('auth.reset_password', token=token, _external=True)
            flash(f'🔗 Link de recuperación (SOLO DESARROLLO): {reset_link}', 'info')
            flash('Se ha enviado un correo con instrucciones para restablecer tu contraseña.', 'success')
        else:
            flash('Si el correo existe en nuestro sistema, recibirás instrucciones.', 'info')
        
        return redirect(url_for('auth.forgot_password'))
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """🔑 Restablecer contraseña con token"""
    email = verify_reset_token(token)
    
    if not email:
        flash('El link de recuperación ha expirado o es inválido. Solicita uno nuevo.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Usuario no encontrado.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if password != confirm_password:
            flash('Las contraseñas no coinciden.', 'error')
            return redirect(url_for('auth.reset_password', token=token))
        
        is_valid, message = validate_password_strength(password)
        if not is_valid:
            flash(message, 'error')
            return redirect(url_for('auth.reset_password', token=token))
        
        user.set_password(password)
        db.session.commit()
        
        flash('¡Contraseña actualizada exitosamente! Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', token=token)