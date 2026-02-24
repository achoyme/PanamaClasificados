import redis
from functools import wraps
from flask import request, jsonify, abort, flash, redirect, url_for
from flask_login import current_user

# ==========================================
# CONEXIÓN A REDIS
# ==========================================
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()  # Probamos si Redis está vivo
except redis.ConnectionError:
    print("⚠️ Advertencia: El motor Redis no está corriendo. El Rate Limiting está en modo pasivo.")
    redis_client = None

# ==========================================
# DECORADOR: RATE LIMITING (Anti-Spam)
# ==========================================
def rate_limit(limit=5, per_seconds=60, key_prefix='rl'):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not redis_client:
                return f(*args, **kwargs)
            
            identifier = str(current_user.id) if current_user.is_authenticated else request.remote_addr
            key = f"{key_prefix}:{request.endpoint}:{identifier}"
            
            current = redis_client.get(key)
            
            if current and int(current) >= limit:
                ttl = redis_client.ttl(key)
                if request.is_json:
                    return jsonify({
                        'success': False, 
                        'error': f'Límite de peticiones excedido. Intenta de nuevo en {ttl} segundos.'
                    }), 429
                
                flash(f'Has realizado demasiadas acciones. Por favor, espera {ttl} segundos.', 'error')
                return redirect(request.referrer or url_for('main.index'))
            
            pipe = redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, per_seconds)
            pipe.execute()
            
            return f(*args, **kwargs)
        return wrapped
    return decorator

# ==========================================
# DECORADORES DE ROLES (Moderador y Admin)
# ==========================================
def moderator_required(f):
    """Permite el acceso solo a moderadores o administradores."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or (not current_user.is_moderator and not current_user.is_admin):
            abort(403) # Lanza error de "Acceso Denegado"
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Permite el acceso exclusivamente a administradores."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
