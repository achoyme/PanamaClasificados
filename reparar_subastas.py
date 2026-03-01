import os
from dotenv import load_dotenv
load_dotenv()

from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Reparando base de datos de Subastas...")
    try:
        # Inyectamos las columnas faltantes a la fuerza en PostgreSQL
        queries = [
            "ALTER TABLE auctions ADD COLUMN IF NOT EXISTS minimum_acceptable_price NUMERIC(10, 2);",
            "ALTER TABLE auctions ADD COLUMN IF NOT EXISTS seller_acceptance_status VARCHAR(20) DEFAULT 'Pending';",
            "ALTER TABLE auctions ADD COLUMN IF NOT EXISTS seller_acceptance_date TIMESTAMP;",
            "ALTER TABLE auctions ADD COLUMN IF NOT EXISTS rejection_reason VARCHAR(500);",
            "ALTER TABLE auctions ADD COLUMN IF NOT EXISTS terms_accepted BOOLEAN DEFAULT TRUE;",
            "ALTER TABLE auctions ADD COLUMN IF NOT EXISTS terms_version VARCHAR(10) DEFAULT '1.0';"
        ]
        
        for query in queries:
            db.session.execute(text(query))
            
        db.session.commit()
        print("✅ ¡Éxito! Las columnas de la subasta han sido inyectadas en la base de datos.")
    except Exception as e:
        db.session.rollback()
        print("⚠️ Hubo un error al alterar la tabla:", e)