import os
from dotenv import load_dotenv
load_dotenv()

from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Reparando base de datos...")
    try:
        # Inyectamos la columna a la fuerza en PostgreSQL
        db.session.execute(text("ALTER TABLE users ADD COLUMN account_type VARCHAR(50) DEFAULT 'Particular';"))
        db.session.commit()
        print("✅ ¡Éxito! La columna 'account_type' ha sido creada.")
    except Exception as e:
        db.session.rollback()
        print("⚠️ Nota: La columna ya existía o hubo un error:", e)