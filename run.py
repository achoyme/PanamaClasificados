#!/usr/bin/env python3
import eventlet
eventlet.monkey_patch()

from app import create_app
from app.extensions import db, socketio
from app.models import User, Listing, Category, Report, AIAnalysis
import os

app = create_app(os.getenv('FLASK_ENV', 'development'))

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Listing': Listing, 'Category': Category, 'Report': Report, 'AIAnalysis': AIAnalysis}

@app.cli.command()
def init_db():
    db.create_all()
    categories = [
        Category(name='Electrónica', slug='electronica', icon_name='smartphone', display_order=1),
        Category(name='Vehículos', slug='vehiculos', icon_name='directions_car', display_order=2),
        Category(name='Inmuebles', slug='inmuebles', icon_name='home', display_order=3),
        Category(name='Moda', slug='moda', icon_name='checkroom', display_order=4),
        Category(name='Hogar', slug='hogar', icon_name='chair', display_order=5),
    ]
    for cat in categories:
        if not Category.query.filter_by(slug=cat.slug).first():
            db.session.add(cat)
    
    admin = User.query.filter_by(email='admin@panamaclassifieds.com').first()
    if not admin:
        admin = User(
            email='admin@panamaclassifieds.com', first_name='Admin', last_name='Sistema',
            is_admin=True, is_moderator=True, is_verified=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
    
    db.session.commit()
    print('✅ Base de datos inicializada correctamente')

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
