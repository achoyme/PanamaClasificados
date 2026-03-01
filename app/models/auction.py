from app import db
from datetime import datetime

class Auction(db.Model):
    __tablename__ = 'auctions'
    
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    start_price = db.Column(db.Numeric(10, 2), nullable=False)
    current_price = db.Column(db.Numeric(10, 2), nullable=False)
    buy_now_price = db.Column(db.Numeric(10, 2))
    
    # ✅ ESTILO EBAY: Precio de Reserva (oculto) y Costo de Envío
    reserve_price = db.Column(db.Numeric(10, 2))
    shipping_cost = db.Column(db.Numeric(10, 2), default=0.00)
    
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='Active') # Active, Ended, Unsold
    winner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    platform_fee_percent = db.Column(db.Numeric(4, 2), default=5.00)
    
    # Relaciones
    listing = db.relationship('Listing', back_populates='auction')
    seller = db.relationship('User', foreign_keys=[seller_id], backref='auctions_created')
    winner = db.relationship('User', foreign_keys=[winner_id], backref='auctions_won')
    bids = db.relationship('Bid', back_populates='auction', lazy='dynamic', order_by='Bid.max_auto_bid.desc()')

class Bid(db.Model):
    __tablename__ = 'bids'
    
    id = db.Column(db.Integer, primary_key=True)
    auction_id = db.Column(db.Integer, db.ForeignKey('auctions.id'), nullable=False)
    bidder_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # ✅ ESTILO EBAY: Puja actual y la Puja Máxima del usuario
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    max_auto_bid = db.Column(db.Numeric(10, 2), nullable=False)
    is_auto_bid = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    auction = db.relationship('Auction', back_populates='bids')
    bidder = db.relationship('User', backref='bids')