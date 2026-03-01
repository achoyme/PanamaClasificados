import os
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.auction import Auction, Bid
from app.models import Listing
from app import db, socketio
from flask_socketio import emit, join_room
from datetime import datetime, timedelta
from decimal import Decimal

auctions_bp = Blueprint('auctions', __name__, url_prefix='/subastas')

def get_minimum_increment(current_price):
    """Calcula el incremento mínimo estilo eBay basado en el precio actual"""
    if current_price < 10: return Decimal('0.50')
    if current_price < 50: return Decimal('1.00')
    if current_price < 250: return Decimal('2.50')
    if current_price < 1000: return Decimal('5.00')
    return Decimal('10.00')

@auctions_bp.route('/')
def index():
    now = datetime.utcnow()
    active_auctions = Auction.query.filter(
        Auction.status == 'Active',
        Auction.end_time > now
    ).order_by(Auction.end_time.asc()).all()
    
    ending_soon = Auction.query.filter(
        Auction.status == 'Active',
        Auction.end_time > now,
        Auction.end_time <= now + timedelta(hours=1)
    ).order_by(Auction.end_time.asc()).limit(6).all()
    
    my_won_auctions = []
    if current_user.is_authenticated:
        my_won_auctions = Auction.query.filter_by(winner_id=current_user.id, status='Ended').all()
    
    return render_template('auctions/index.html', auctions=active_auctions, ending_soon=ending_soon, my_won_auctions=my_won_auctions, now=now)

@auctions_bp.route('/crear/<int:listing_id>', methods=['GET', 'POST'])
@login_required
def create(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    if listing.user_id != current_user.id:
        flash('No autorizado', 'error')
        return redirect(url_for('listings.my_listings'))
    
    if listing.auction:
        return redirect(url_for('auctions.detail', auction_id=listing.auction.id))
    
    if request.method == 'POST':
        start_price = Decimal(request.form.get('start_price', 0))
        buy_now = request.form.get('buy_now_price')
        reserve_price = request.form.get('reserve_price')
        shipping_cost = Decimal(request.form.get('shipping_cost', 0))
        duration_hours = int(request.form.get('duration_hours', 168)) 
        
        auction = Auction(
            listing_id=listing.id,
            seller_id=current_user.id,
            start_price=start_price,
            current_price=start_price,
            buy_now_price=Decimal(buy_now) if buy_now else None,
            reserve_price=Decimal(reserve_price) if reserve_price else None,
            shipping_cost=shipping_cost,
            end_time=datetime.utcnow() + timedelta(hours=duration_hours)
        )
        db.session.add(auction)
        listing.status = 'Auction'
        db.session.commit()
        flash('¡Subasta publicada con éxito!', 'success')
        return redirect(url_for('auctions.detail', auction_id=auction.id))
    
    return render_template('auctions/create.html', listing=listing, now=datetime.utcnow())

@auctions_bp.route('/<int:auction_id>')
def detail(auction_id):
    auction = Auction.query.get_or_404(auction_id)
    now = datetime.utcnow()
    
    # Cierre Automático Estilo eBay
    if auction.status == 'Active' and auction.end_time <= now:
        if auction.reserve_price and auction.current_price < auction.reserve_price:
            auction.status = 'Unsold' 
        else:
            highest_bid = auction.bids.order_by(Bid.max_auto_bid.desc()).first()
            if highest_bid:
                auction.status = 'Ended'
                auction.winner_id = highest_bid.bidder_id
            else:
                auction.status = 'Unsold'
        db.session.commit()

    top_bids = auction.bids.order_by(Bid.amount.desc(), Bid.created_at.asc()).limit(10).all()
    min_increment = get_minimum_increment(auction.current_price)
    min_next_bid = auction.current_price + min_increment if auction.bids.count() > 0 else auction.start_price
    
    user_highest_bid = Bid.query.filter_by(auction_id=auction.id, bidder_id=current_user.id).order_by(Bid.max_auto_bid.desc()).first() if current_user.is_authenticated else None

    # Variable para la plantilla que indica si estamos en desarrollo
    is_dev = os.getenv('FLASK_ENV', 'development').lower() == 'development'

    return render_template('auctions/detail.html', auction=auction, bids=top_bids, now=now, min_next_bid=min_next_bid, user_highest_bid=user_highest_bid, is_dev=is_dev)

@auctions_bp.route('/<int:auction_id>/pujar', methods=['POST'])
@login_required
def place_bid(auction_id):
    auction = Auction.query.get_or_404(auction_id)
    
    if auction.status != 'Active' or auction.end_time < datetime.utcnow():
        return jsonify({'success': False, 'error': 'La subasta ha finalizado.'}), 400
    
    if auction.seller_id == current_user.id:
        return jsonify({'success': False, 'error': 'Política Anti-Fraude: No puedes pujar en tu propia subasta.'}), 400
        
    # ✅ NUEVO: ESCUDO ANTI-FRAUDE NIVEL 2 (Rastreo IP) Inteligente
    is_production = os.getenv('FLASK_ENV', 'development').lower() == 'production'
    if is_production:
        if current_user.last_ip_address and auction.seller.last_ip_address:
            if current_user.last_ip_address == auction.seller.last_ip_address:
                return jsonify({'success': False, 'error': '🛡️ Alerta Anti-Fraude: Tu conexión de red (IP) es idéntica a la del vendedor. Puja bloqueada por sospecha de manipulación de precio.'}), 400
    
    max_bid = Decimal(request.form.get('amount', 0))
    increment = get_minimum_increment(auction.current_price)
    min_allowed = auction.current_price + increment if auction.bids.count() > 0 else auction.start_price
    
    if max_bid < min_allowed:
        return jsonify({'success': False, 'error': f'Debes introducir una puja máxima de al menos ${min_allowed}'}), 400
    
    current_leader = auction.bids.order_by(Bid.max_auto_bid.desc(), Bid.created_at.asc()).first()
    
    if not current_leader:
        auction.current_price = auction.start_price
        new_bid = Bid(auction_id=auction.id, bidder_id=current_user.id, amount=auction.current_price, max_auto_bid=max_bid)
        db.session.add(new_bid)
        if not auction.reserve_price or max_bid >= auction.reserve_price:
            auction.buy_now_price = None 
    else:
        if current_leader.bidder_id == current_user.id:
            current_leader.max_auto_bid = max_bid
            db.session.commit()
            return jsonify({'success': True, 'new_price': str(auction.current_price), 'msg': 'Límite máximo actualizado con éxito.'})
        
        if max_bid > current_leader.max_auto_bid:
            new_price = min(max_bid, current_leader.max_auto_bid + increment)
            auction.current_price = new_price
            new_bid = Bid(auction_id=auction.id, bidder_id=current_user.id, amount=new_price, max_auto_bid=max_bid)
            db.session.add(new_bid)
            if not auction.reserve_price or max_bid >= auction.reserve_price:
                auction.buy_now_price = None
        else:
            new_price = min(current_leader.max_auto_bid, max_bid + increment)
            auction.current_price = new_price
            current_leader.amount = new_price
            failed_bid = Bid(auction_id=auction.id, bidder_id=current_user.id, amount=max_bid, max_auto_bid=max_bid, is_auto_bid=False)
            db.session.add(failed_bid)
            db.session.commit()
            return jsonify({'success': False, 'error': f'Has sido superado inmediatamente por la puja automática de otro usuario. Puja actual: ${new_price}'}), 400
            
    db.session.commit()
    socketio.emit('new_bid', {'amount': str(auction.current_price)}, room=f'auction_{auction.id}')
    return jsonify({'success': True, 'new_price': str(auction.current_price)})

@auctions_bp.route('/<int:auction_id>/comprar-ahora', methods=['POST'])
@login_required
def buy_now(auction_id):
    auction = Auction.query.get_or_404(auction_id)
    if not auction.buy_now_price: return jsonify({'success': False, 'error': 'No disponible'}), 400
    if auction.seller_id == current_user.id: return jsonify({'success': False, 'error': 'Anti-fraude'}), 400
    
    # ✅ Anti-Fraude Nivel 2 para "Comprar Ahora"
    is_production = os.getenv('FLASK_ENV', 'development').lower() == 'production'
    if is_production:
        if current_user.last_ip_address and auction.seller.last_ip_address:
            if current_user.last_ip_address == auction.seller.last_ip_address:
                flash('🛡️ Alerta Anti-Fraude: Tu IP coincide con la del vendedor.', 'error')
                return redirect(url_for('auctions.detail', auction_id=auction.id))

    auction.status = 'Ended'
    auction.winner_id = current_user.id
    auction.current_price = auction.buy_now_price
    db.session.commit()
    flash('¡Has comprado el artículo exitosamente!', 'success')
    return redirect(url_for('auctions.checkout', auction_id=auction.id))

@auctions_bp.route('/<int:auction_id>/checkout')
@login_required
def checkout(auction_id):
    auction = Auction.query.get_or_404(auction_id)
    if auction.winner_id != current_user.id and auction.seller_id != current_user.id:
        flash('Acceso denegado', 'error')
        return redirect(url_for('auctions.index'))
        
    subtotal = auction.current_price
    shipping = auction.shipping_cost
    fee = subtotal * (auction.platform_fee_percent / Decimal('100'))
    total = subtotal + shipping + fee
    
    return render_template('auctions/checkout.html', auction=auction, subtotal=subtotal, shipping=shipping, fee=fee, total=total)

@socketio.on('join_auction')
def on_join_auction(data):
    room = f"auction_{data['auction_id']}"
    join_room(room)
    emit('joined', {'room': room})