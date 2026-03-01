import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Cargamos las variables de entorno
load_dotenv()

from app import create_app, db
from app.models.user import User
from app.models.listing import Listing, Image, Category

# Inicializamos la aplicación
app = create_app()

with app.app_context():
    print("🚀 Iniciando generador automático de artículos de prueba...")

    # 1. Buscar al usuario administrador (o cualquier usuario existente)
    user = User.query.filter_by(email="admin@panamaclassifieds.com").first()
    if not user:
        print("⚠️ No encontré al usuario admin@panamaclassifieds.com.")
        user = User.query.first() # Toma el primer usuario que encuentre
        if not user:
            print("❌ No hay ningún usuario en la base de datos. Registra uno primero o corre 'python seed_db.py'.")
            exit()

    # 2. Buscar las categorías
    categorias = Category.query.all()
    if not categorias:
        print("❌ No hay categorías en la base de datos. Ejecuta 'python seed_db.py' primero.")
        exit()

    # 3. Base de datos falsa para crear anuncios variados
    productos_base = [
        {"title": "Toyota Hilux Automática", "desc": "Camioneta en excelente estado, un solo dueño. Mantenimientos al día en agencia. Llantas nuevas.", "price": 18500, "cond": "Usado - Buen Estado", "prov": "Panamá", "dist": "San Francisco"},
        {"title": "iPhone 13 Pro Max 256GB", "desc": "Teléfono como nuevo, sin detalles ni rayones. Incluye caja, cargador original y 3 covers de regalo.", "price": 750, "cond": "Usado - Como Nuevo", "prov": "Panamá", "dist": "Betania"},
        {"title": "Apartamento Amoblado 2 Rec", "desc": "Hermoso apartamento, full amoblado, céntrico, cerca de estación del metro. Área social completa.", "price": 145000, "cond": "Nuevo", "prov": "Panamá", "dist": "Bella Vista"},
        {"title": "PlayStation 5 + 2 Controles", "desc": "Consola PS5 edición disco. Poco uso, funciona perfecto. Incluye dos juegos físicos.", "price": 480, "cond": "Usado - Buen Estado", "prov": "Panamá Oeste", "dist": "Arraiján"},
        {"title": "Sofá de Cuero Genuino", "desc": "Sofá elegante tipo L, muy cómodo. Se vende por mudanza al extranjero.", "price": 320, "cond": "Usado - Aceptable", "prov": "Chiriquí", "dist": "David"},
        {"title": "Laptop Dell Inspiron Core i7", "desc": "Ideal para estudiantes, universidad o teletrabajo. 16GB RAM, 512GB SSD. Batería dura 4 horas.", "price": 550, "cond": "Usado - Buen Estado", "prov": "Coclé", "dist": "Penonomé"},
        {"title": "Bicicleta Montañera Trek", "desc": "Bicicleta aro 29, frenos de disco hidráulicos, suspensión delantera. Lista para la montaña.", "price": 280, "cond": "Usado - Como Nuevo", "prov": "Herrera", "dist": "Chitré"},
        {"title": "Reloj Smartwatch Garmin", "desc": "Reloj deportivo con GPS y monitor de ritmo cardíaco. Resistente al agua.", "price": 150, "cond": "Nuevo", "prov": "Los Santos", "dist": "Las Tablas"}
    ]

    print(f"Inyectando 30 anuncios en la cuenta de: {user.first_name}...")

    # Vamos a crear 30 anuncios (así activamos la paginación que suele cortar en 20 artículos)
    anuncios_creados = 0
    for i in range(30):
        # Elegir un producto base y una categoría al azar
        base = random.choice(productos_base)
        cat = random.choice(categorias)
        
        # Crear el anuncio
        nuevo_anuncio = Listing(
            user_id=user.id,
            category_id=cat.id,
            title=f"{base['title']} - Oferta #{i+1}",
            description=f"{base['desc']}\n\nPrecio negociable para compradores serios. ID de publicación temporal: PC-{random.randint(1000, 9999)}.",
            price=base['price'] + random.randint(-50, 150), # Variamos un poco el precio
            province=base['prov'],
            district=base['dist'],
            condition=base['cond'],
            status='Active',
            is_negotiable=random.choice([True, False]),
            tier=random.choice(['Gratis', 'Gratis', 'Gratis', 'Profesional', 'Premium']), # Hacemos que algunos sean destacados
            duration_days=30,
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        
        db.session.add(nuevo_anuncio)
        db.session.flush() # Flush guarda temporalmente en BD para darnos el 'nuevo_anuncio.id'
        
        # Crear 3 imágenes por cada anuncio usando un servicio de imágenes de relleno (Picsum)
        for img_idx in range(3):
            # Picsum usa un 'seed' para generar siempre la misma imagen aleatoria basada en un texto.
            # Usamos el ID del anuncio y el índice para que cada foto sea única.
            img_url = f"https://picsum.photos/seed/Anuncio{nuevo_anuncio.id}Foto{img_idx}/800/600"
            
            nueva_imagen = Image(
                listing_id=nuevo_anuncio.id,
                image_url=img_url,
                thumbnail_url=f"https://picsum.photos/seed/Anuncio{nuevo_anuncio.id}Foto{img_idx}/200/200",
                display_order=img_idx,
                is_primary=(img_idx == 0)
            )
            db.session.add(nueva_imagen)
            
        anuncios_creados += 1

    # Confirmamos todos los cambios en la base de datos
    db.session.commit()
    print("==================================================")
    print(f"🎉 ¡Éxito! Se han inyectado {anuncios_creados} anuncios de prueba.")
    print("==================================================")
    print("Ya puedes encender tu servidor e ir a la sección 'Explorar'.")