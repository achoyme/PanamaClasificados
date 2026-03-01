import redis
from functools import wraps
from flask import request, jsonify, abort, flash, redirect, url_for
from flask_login import current_user

# ==========================================
# CONEXIÓN A REDIS PARA RATE LIMITING
# ==========================================
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
except redis.ConnectionError:
    print("⚠️ Advertencia: Redis no está corriendo. Rate Limiting en modo pasivo.")
    redis_client = None

# ==========================================
# DECORADOR: RATE LIMITING (Anti-Spam)
# ==========================================
def rate_limit(limit=5, per_seconds=60, key_prefix='rl'):
    """
    🛡️ Limita número de peticiones por usuario/IP
    
    Args:
        limit: Máximo de peticiones permitidas
        per_seconds: Ventana de tiempo en segundos
        key_prefix: Prefijo para la clave en Redis
    
    Returns:
        Decorador que aplica el límite
    """
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
                        'error': f'Límite excedido. Intenta en {ttl} segundos.'
                    }), 429
                flash(f'Demasiadas acciones. Espera {ttl} segundos.', 'error')
                return redirect(request.referrer or url_for('main.index'))
            
            pipe = redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, per_seconds)
            pipe.execute()
            
            return f(*args, **kwargs)
        return wrapped
    return decorator

# ==========================================
# DECORADOR: REQUIERE MODERADOR
# ==========================================
def moderator_required(f):
    """
    🔐 Permite acceso solo a moderadores o administradores
    
    Returns:
        403 si el usuario no tiene permisos
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or (not current_user.is_moderator and not current_user.is_admin):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# ==========================================
# DECORADOR: REQUIERE ADMIN
# ==========================================
def admin_required(f):
    """
    🔒 Permite acceso exclusivamente a administradores
    
    Returns:
        403 si el usuario no es admin
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function