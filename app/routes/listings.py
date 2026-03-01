from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app.models import Listing, Category, User, Image, Question # Importamos Question
from app.services.listing_service import ListingService
from app.utils.decorators import rate_limit
from app import db
from app.forms import ListingValidatorForm
# CAMBIO: Importamos 'func' para poder contar los anuncios dinámicamente
from sqlalchemy import func

listings_bp = Blueprint('listings', __name__, url_prefix='/listings')
listing_service = ListingService()

@listings_bp.route('/')
def index():
    filters = {
        'search_term': request.args.get('search', ''),
        'province': request.args.get('province', ''),
        'district': request.args.get('district', ''),
        'category_id': request.args.get('category_id', type=int),
        'page': request.args.get('page', 1, type=int)
    }
    
    # CAMBIO: En lugar de Category.query.all(), hacemos un "Join" para contar los anuncios activos.
    categories_query = db.session.query(
        Category.id, 
        Category.name, 
        func.count(Listing.id).label('total_listings')
    ).outerjoin(Listing, (Listing.category_id == Category.id) & (Listing.status.in_(['Active', 'Auction'])))\
     .group_by(Category.id).all()
    
    # Convertimos el resultado a una lista de diccionarios para que Jinja lo entienda
    categories = [{'id': c.id, 'name': c.name, 'total_listings': c.total_listings} for c in categories_query]

    result = listing_service.search_listings(filters)
    
    return render_template('listings/index.html', 
                           listings=result['listings'], 
                           total=result['total'], 
                           pages=result['pages'], 
                           current_page=result['current_page'],
                           categories=categories,
                           filters=filters)

@listings_bp.route('/<int:listing_id>')
def details(listing_id):
    listing = listing_service.get_listing_by_id(listing_id)
    if not listing:
        flash('Anuncio no encontrado.', 'error')
        return redirect(url_for('main.index'))
        
    # ✅ CORRECCIÓN: Agregamos now=datetime.utcnow() para que la plantilla no colapse con subastas
    return render_template('listings/details.html', listing=listing, now=datetime.utcnow())

# ==========================================
# PREGUNTAS Y RESPUESTAS (MERCADOLIBRE)
# ==========================================
@listings_bp.route('/<int:listing_id>/ask', methods=['POST'])
@login_required
@rate_limit(limit=10, per_seconds=60)
def ask_question(listing_id):
    content = request.form.get('content')
    if content:
        question = Question(listing_id=listing_id, user_id=current_user.id, content=content)
        db.session.add(question)
        db.session.commit()
        flash('¡Tu pregunta ha sido enviada! El vendedor te responderá pronto.', 'success')
    return redirect(url_for('listings.details', listing_id=listing_id))

@listings_bp.route('/question/<int:question_id>/answer', methods=['POST'])
@login_required
def answer_question(question_id):
    question = Question.query.get_or_404(question_id)
    
    # Seguridad: Solo el dueño del anuncio puede responder
    if question.listing.user_id != current_user.id:
        flash('No tienes permiso para responder esta pregunta.', 'error')
        return redirect(url_for('listings.details', listing_id=question.listing_id))
    
    answer = request.form.get('answer')
    if answer:
        question.answer = answer
        question.answered_at = datetime.utcnow()
        db.session.commit()
        flash('Respuesta publicada exitosamente.', 'success')
    
    return redirect(url_for('listings.details', listing_id=question.listing_id))

# ==========================================
# MENSAJERÍA PRIVADA
# ==========================================
@listings_bp.route('/<int:listing_id>/contact', methods=['POST'])
@rate_limit(limit=5, per_seconds=3600)
def contact_seller(listing_id):
    from app.models import ContactMessage
    listing = listing_service.get_listing_by_id(listing_id)
    if listing:
        try:
            msg = ContactMessage(
                listing_id=listing.id,
                sender_name=request.form.get('buyer_name'),
                sender_email=request.form.get('buyer_email'),
                sender_phone=request.form.get('buyer_phone'),
                content=request.form.get('buyer_message')
            )
            db.session.add(msg)
            db.session.commit()
            flash(f'¡Tu mensaje ha sido enviado exitosamente al vendedor ({listing.user.first_name})!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al enviar el mensaje. Intenta de nuevo.', 'error')
            
    return redirect(url_for('listings.details', listing_id=listing_id))

@listings_bp.route('/create', methods=['GET', 'POST'])
@login_required
@rate_limit(limit=10, per_seconds=3600)
def create():
    categories = Category.query.all()
    
    if request.method == 'POST':
        form = ListingValidatorForm(request.form)
        if not form.validate():
            for field, errors in form.errors.items():
                for error in errors: flash(f"{error}", 'error')
            return render_template('listings/create.html', categories=categories, listing=None)

        data = request.form.to_dict()
        data['user_id'] = current_user.id
        images = request.files.getlist('images')
        virtual_tour = request.files.get('virtual_tour')
        
        result = listing_service.create_listing(data, images, virtual_tour_file=virtual_tour)
        if result['success']:
            flash('¡Tu anuncio ha sido publicado con éxito!', 'success')
            return redirect(url_for('listings.details', listing_id=result['listing']['id']))
        else:
            flash(f"Error al publicar: {result.get('error')}", 'error')
            
    return render_template('listings/create.html', categories=categories, listing=None)

@listings_bp.route('/<int:listing_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(listing_id):
    listing = listing_service.get_listing_by_id(listing_id)
    if not listing or listing.user_id != current_user.id:
        flash('No tienes permiso para editar este anuncio.', 'error')
        return redirect(url_for('listings.my_listings'))
        
    categories = Category.query.all()
    
    if request.method == 'POST':
        form = ListingValidatorForm(request.form)
        if not form.validate():
            for field, errors in form.errors.items():
                for error in errors: flash(f"{error}", 'error')
            return render_template('listings/create.html', categories=categories, listing=listing)

        data = request.form.to_dict()
        images = request.files.getlist('images')
        virtual_tour = request.files.get('virtual_tour') 
        
        result = listing_service.update_listing(listing_id, current_user.id, data, images, virtual_tour_file=virtual_tour)
        if result['success']:
            flash('Anuncio actualizado correctamente.', 'success')
            return redirect(url_for('listings.details', listing_id=listing_id))
        else:
            flash(f"Error al actualizar: {result.get('error')}", 'error')
            
    return render_template('listings/create.html', categories=categories, listing=listing)

@listings_bp.route('/image/<int:image_id>/delete', methods=['POST'])
@login_required
def delete_image(image_id):
    success = listing_service.delete_image(image_id, current_user.id)
    return jsonify({'success': success})

@listings_bp.route('/<int:listing_id>/mark-sold', methods=['POST'])
@login_required
def mark_sold(listing_id):
    listing = Listing.query.get(listing_id)
    if listing and (listing.user_id == current_user.id or current_user.is_admin):
        listing.status = 'Sold'
        listing.expires_at = datetime.utcnow() + timedelta(hours=24)
        db.session.commit()
        flash('¡Felicidades por tu venta! El anuncio se ha marcado como VENDIDO y se retirará automáticamente en 24 horas.', 'success')
    return redirect(url_for('listings.my_listings'))

@listings_bp.route('/<int:listing_id>/delete', methods=['POST'])
@login_required
def delete(listing_id):
    listing = Listing.query.get(listing_id)
    if listing and (listing.user_id == current_user.id or current_user.is_admin):
        listing.status = 'Deleted'
        db.session.commit()
        flash('Anuncio eliminado permanentemente.', 'success')
    return redirect(url_for('listings.my_listings'))

@listings_bp.route('/my-listings')
@login_required
def my_listings():
    listings = Listing.query.filter_by(user_id=current_user.id).filter(Listing.status != 'Deleted').order_by(Listing.created_at.desc()).all()
    return render_template('listings/my_listings.html', listings=listings, now=datetime.utcnow())

@listings_bp.route('/api/realtime-analysis', methods=['POST'])
@login_required
def realtime_analysis():
    data = request.get_json()
    result = listing_service.get_realtime_analysis(data.get('title', ''), data.get('description', ''))
    return jsonify({'success': True, 'data': result})