from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app.services.listing_service import ListingService
from app.models import Category, Listing
from app import db

listings_bp = Blueprint('listings', __name__, url_prefix='/listings')
listing_service = ListingService()

@listings_bp.route('/')
def index():
    filters = {'search_term': request.args.get('search'), 'category_id': request.args.get('category_id', type=int), 'page': request.args.get('page', 1, type=int)}
    result = listing_service.search_listings(filters)
    return render_template('listings/index.html', listings=result['listings'], filters=filters)

@listings_bp.route('/<int:listing_id>')
def details(listing_id):
    listing = listing_service.get_listing_by_id(listing_id)
    if not listing: return redirect(url_for('listings.index'))
    return render_template('listings/details.html', listing=listing)

@listings_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'GET':
        categories = Category.query.filter_by(is_active=True).all()
        return render_template('listings/create.html', categories=categories)
    
    data = {
        'user_id': current_user.id, 'category_id': request.form.get('category_id', type=int),
        'title': request.form.get('title'), 'description': request.form.get('description'),
        'price': request.form.get('price', type=float), 'province': request.form.get('province'),
        'district': request.form.get('district'), 'city': request.form.get('city'),
        'condition': request.form.get('condition'), 'is_negotiable': request.form.get('is_negotiable') == 'on',
        'image_url_link': request.form.get('image_url_link')
    }
    images = request.files.getlist('images')
    result = listing_service.create_listing(data, images)
    
    if result['success']: return redirect(url_for('listings.details', listing_id=result['listing']['id']))
    return redirect(url_for('listings.create'))

@listings_bp.route('/api/realtime-analysis', methods=['POST'])
@login_required
def realtime_analysis():
    data = request.get_json()
    analysis = listing_service.get_realtime_analysis(data.get('title', ''), data.get('description', ''), data.get('image_urls', []))
    return jsonify({'success': True, 'data': analysis})

@listings_bp.route('/my-listings')
@login_required
def my_listings():
    listings = Listing.query.filter_by(user_id=current_user.id).order_by(Listing.created_at.desc()).all()
    return render_template('listings/my_listings.html', listings=listings)

@listings_bp.route('/<int:listing_id>/delete', methods=['POST'])
@login_required
def delete(listing_id):
    listing = Listing.query.get(listing_id)
    if listing and listing.user_id == current_user.id:
        listing.status = 'Deleted'
        db.session.commit()
    return redirect(url_for('listings.my_listings'))
