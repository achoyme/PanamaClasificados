from functools import wraps
from flask import request, jsonify, abort
from flask_login import current_user
import time

# Memoria para rastrear IPs y ataques
request_history = {}

def rate_limit(limit=5, per_seconds=60):
    """
    Control de Seguridad Anti-Spam: Limita cuántas veces un usuario/IP 
    puede ejecutar una acción para prevenir bots.
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Identificamos al usuario por su ID (si está logueado) o por su IP de red
            identifier = str(current_user.id) if current_user.is_authenticated else request.remote_addr
            now = time.time()
            
            if identifier not in request_history:
                request_history[identifier] = []
                
            # Limpiamos el historial de peticiones antiguas
            request_history[identifier] = [req_time for req_time in request_history[identifier] if now - req_time < per_seconds]
            
            # Si excede el límite, bloqueamos la acción temporalmente
            if len(request_history[identifier]) >= limit:
                if request.is_json:
                    return jsonify({'success': False, 'error': 'Sistema Anti-Spam: Has realizado demasiadas peticiones. Espera un momento.'}), 429
                abort(429, description="Sistema de seguridad activado por exceso de tráfico.")
                
            request_history[identifier].append(now)
            return f(*args, **kwargs)
        return wrapped
    return decorator

def moderator_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or (not current_user.is_moderator and not current_user.is_admin):
            abort(403, description="Acceso denegado. Se requiere nivel de moderador.")
        return f(*args, **kwargs)
    return decorated_function