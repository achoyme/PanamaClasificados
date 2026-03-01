import os
from dotenv import load_dotenv

# 1. ESTO ES LO QUE FALTABA: Obligamos a Python a leer el archivo .env
load_dotenv()

from app import create_app, db
from app.models.user import User

# 2. Inicializamos la aplicación de Flask
app = create_app()

with app.app_context():
    # Revisamos si el admin ya existe para no duplicarlo
    admin_email = "admin@panamaclassifieds.com"
    admin_user = User.query.filter_by(email=admin_email).first()

    if admin_user:
        print(f"✅ El usuario {admin_email} ya existe en la base de datos.")
    else:
        print("⚙️ Creando cuenta de Administrador Supremo...")
        
        nuevo_admin = User(
            email=admin_email,
            first_name="Admin",
            last_name="System",
            phone_number="6000-0000",
            province="Panamá",
            is_verified=True,
            is_admin=True,
            is_moderator=True,
            package_name="Agencia VIP",
            prof_credits=999,
            prem_credits=999
        )
        # Encriptamos la contraseña
        nuevo_admin.set_password("admin123")
        
        db.session.add(nuevo_admin)
        db.session.commit()
        
        print("🎉 ¡Administrador creado con éxito!")
        print("-------------------------------------------------")
        print(f"📧 Correo: {admin_email}")
        print("🔑 Clave:  admin123")
        print("-------------------------------------------------")