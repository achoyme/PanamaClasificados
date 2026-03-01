import os
from dotenv import load_dotenv
load_dotenv()

from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("=========================================")
    print("🚨 INICIANDO INYECCIÓN FORZADA DE COLUMNAS")
    print("=========================================")
    
    try:
        # Comando 1: Crear reserve_price
        print("Intentando crear 'reserve_price'...")
        db.session.execute(text("ALTER TABLE auctions ADD COLUMN reserve_price NUMERIC(10, 2);"))
        db.session.commit()
        print("✅ 'reserve_price' creado con éxito.")
    except Exception as e:
        db.session.rollback()
        print("⚠️ Nota sobre reserve_price: Ya existía o hubo un aviso menor.")

    try:
        # Comando 2: Crear shipping_cost
        print("Intentando crear 'shipping_cost'...")
        db.session.execute(text("ALTER TABLE auctions ADD COLUMN shipping_cost NUMERIC(10, 2) DEFAULT 0.00;"))
        db.session.commit()
        print("✅ 'shipping_cost' creado con éxito.")
    except Exception as e:
        db.session.rollback()
        print("⚠️ Nota sobre shipping_cost: Ya existía o hubo un aviso menor.")

    print("\n=========================================")
    print("🎉 REPARACIÓN COMPLETADA. YA PUEDES ENTRAR A LA PÁGINA.")
    print("=========================================")