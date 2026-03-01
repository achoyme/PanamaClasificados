import os
from dotenv import load_dotenv
load_dotenv()
from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("🚀 Actualizando Base de Datos a la arquitectura estilo eBay...")
    try:
        queries = [
            "ALTER TABLE auctions ADD COLUMN IF NOT EXISTS reserve_price NUMERIC(10, 2);",
            "ALTER TABLE auctions ADD COLUMN IF NOT EXISTS shipping_cost NUMERIC(10, 2) DEFAULT 0.00;"
        ]
        for query in queries:
            db.session.execute(text(query))
        db.session.commit()
        print("✅ ¡Éxito! Tu base de datos ahora soporta Reservas y Envíos estilo eBay.")
    except Exception as e:
        db.session.rollback()
        print("⚠️ Nota:", e)