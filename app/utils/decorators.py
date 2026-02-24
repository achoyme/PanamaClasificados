import redis
from functools import wraps
from flask import request, jsonify, abort, flash, redirect, url_for
from flask_login import current_user

# Conexión a Redis
# Si estás en Windows local sin Redis instalado, el bloque 'try' evitará que la app colapse.
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()  # Probamos si Redis está vivo
except redis.ConnectionError:
    print("⚠️ Advertencia: El motor Redis no está corriendo. El Rate Limiting está en modo pasivo.")
    redis_client = None

def rate_limit(limit=5, per_seconds=60, key_prefix='rl'):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Si Redis no está disponible (ej. en desarrollo local), permitimos el paso
            if not redis_client:
                return f(*args, **kwargs)
            
            # Identificamos al usuario por su ID o por su IP si es visitante
            identifier = str(current_user.id) if current_user.is_authenticated else request.remote_addr
            key = f"{key_prefix}:{request.endpoint}:{identifier}"
            
            current = redis_client.get(key)
            
            # Si superó el límite, lo bloqueamos
            if current and int(current) >= limit:
                ttl = redis_client.ttl(key)
                if request.is_json:
                    return jsonify({
                        'success': False, 
                        'error': f'Límite de peticiones excedido. Intenta de nuevo en {ttl} segundos.'
                    }), 429
                
                flash(f'Has realizado demasiadas acciones. Por favor, espera {ttl} segundos.', 'error')
                return redirect(request.referrer or url_for('main.index'))
            
            # Registramos la petición atómica con pipeline para máxima velocidad
            pipe = redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, per_seconds)
            pipe.execute()
            
            return f(*args, **kwargs)
        return wrapped
    return decorator
