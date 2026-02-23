from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import Listing, Category
from app.services.listing_service import ListingService
from app.utils.decorators import rate_limit

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
    categories = Category.query.all()
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
    return render_template('listings/details.html', listing=listing)

@listings_bp.route('/create', methods=['GET', 'POST'])
@login_required
@rate_limit(limit=10, per_seconds=3600)
def create():
    categories = Category.query.all()
    
    if request.method == 'POST':
        data = request.form.to_dict()
        data['user_id'] = current_user.id
        
        # Atrapamos todas las imágenes normales
        images = request.files.getlist('images')
        
        # ¡AQUÍ ESTÁ LA MAGIA! Atrapamos la imagen 360° del formulario
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
        data = request.form.to_dict()
        images = request.files.getlist('images')
        virtual_tour = request.files.get('virtual_tour') # Atrapamos el 360 en la edición también
        
        result = listing_service.update_listing(listing_id, current_user.id, data, images, virtual_tour_file=virtual_tour)
        
        if result['success']:
            flash('Anuncio actualizado correctamente.', 'success')
            return redirect(url_for('listings.details', listing_id=listing_id))
        else:
            flash(f"Error al actualizar: {result.get('error')}", 'error')
            
    return render_template('listings/create.html', categories=categories, listing=listing)

@listings_bp.route('/<int:listing_id>/delete', methods=['POST'])
@login_required
def delete(listing_id):
    from app import db
    listing = Listing.query.get(listing_id)
    if listing and (listing.user_id == current_user.id or current_user.is_admin):
        listing.status = 'Deleted'
        db.session.commit()
        flash('Anuncio eliminado.', 'success')
    return redirect(url_for('listings.my_listings'))

@listings_bp.route('/my-listings')
@login_required
def my_listings():
    listings = Listing.query.filter_by(user_id=current_user.id).filter(Listing.status != 'Deleted').order_by(Listing.created_at.desc()).all()
    from datetime import datetime
    return render_template('listings/my_listings.html', listings=listings, now=datetime.utcnow())

@listings_bp.route('/api/realtime-analysis', methods=['POST'])
@login_required
def realtime_analysis():
    data = request.get_json()
    result = listing_service.get_realtime_analysis(data.get('title', ''), data.get('description', ''))
    return jsonify({'success': True, 'data': result})