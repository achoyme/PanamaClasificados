import os
from dotenv import load_dotenv
load_dotenv()
from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("🚨 Preparando Base de Datos para Rastreo de IP...")
    try:
        db.session.execute(text("ALTER TABLE users ADD COLUMN last_ip_address VARCHAR(45);"))
        db.session.commit()
        print("✅ ¡Éxito! Columna 'last_ip_address' creada. El sistema ahora rastreará IPs.")
    except Exception as e:
        db.session.rollback()
        print("⚠️ Nota: La columna ya existía o hubo un aviso menor.")