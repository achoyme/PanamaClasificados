import os
import re
import unicodedata
from dotenv import load_dotenv

# Obligamos a Python a leer el archivo .env para las contraseñas
load_dotenv()

from app import create_app, db
from app.models.user import User
from app.models import Category

# Función mágica para crear Slugs (Convierte "Bienes Raíces" a "bienes-raices")
def slugify(text):
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '-', text)

# Inicializamos la aplicación de Flask
app = create_app()

with app.app_context():
    print("=========================================")
    print("🚀 INICIANDO INSTALACIÓN DE DATOS (NUEVA PC)")
    print("=========================================")

    # ---------------------------------------------------------
    # 1. INYECTAR LAS 20 CATEGORÍAS PROFESIONALES
    # ---------------------------------------------------------
    categorias_profesionales = [
        "Bienes Raíces - Ventas",
        "Bienes Raíces - Alquileres",
        "Autos y Camionetas",
        "Motos, Botes y Vehículos Pesados",
        "Accesorios y Repuestos de Autos",
        "Celulares y Accesorios",
        "Computadoras, Laptops y Tablets",
        "Electrónica, Audio y Video",
        "Empleos y Búsqueda de Personal",
        "Servicios Profesionales y Oficios",
        "Hogar, Muebles y Jardín",
        "Moda, Ropa y Calzado",
        "Salud, Belleza y Cuidado Personal",
        "Mascotas y Accesorios",
        "Deportes, Bicicletas y Fitness",
        "Instrumentos Musicales",
        "Arte, Colecciones y Antigüedades",
        "Artículos para Bebés y Niños",
        "Maquinaria y Equipos Comerciales",
        "Otros Clasificados"
    ]

    print("\n📂 Configurando Categorías del Marketplace...")
    categorias_creadas = 0
    for cat_name in categorias_profesionales:
        cat = Category.query.filter_by(name=cat_name).first()
        if not cat:
            # AHORA SÍ: Generamos el slug obligatorio y lo enviamos a la Base de Datos
            mi_slug = slugify(cat_name)
            nueva_cat = Category(name=cat_name, slug=mi_slug)
            db.session.add(nueva_cat)
            categorias_creadas += 1
    
    # Guardamos las categorías
    db.session.commit()
    print(f"✅ Se añadieron {categorias_creadas} categorías nuevas con éxito.")

    # ---------------------------------------------------------
    # 2. INYECTAR EL ADMINISTRADOR SUPREMO
    # ---------------------------------------------------------
    print("\n👤 Configurando Administrador...")
    admin_email = "admin@panamaclassifieds.com"
    admin_user = User.query.filter_by(email=admin_email).first()

    if admin_user:
        print(f"✅ El usuario {admin_email} ya estaba listo.")
    else:
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
        nuevo_admin.set_password("admin123")
        db.session.add(nuevo_admin)
        db.session.commit()
        
        print("🎉 ¡Administrador creado con éxito!")
        print(f"   📧 Correo: {admin_email}")
        print("   🔑 Clave:  admin123")

    print("\n=========================================")
    print("✨ INSTALACIÓN COMPLETADA. ¡YA PUEDES INICIAR!")
    print("=========================================")