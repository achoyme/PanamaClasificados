from app import db
from datetime import datetime

class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    # Quién escribe la reseña (Comprador)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    # A quién le escriben la reseña (Vendedor)
    reviewed_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    rating = db.Column(db.Integer, nullable=False) # 1 al 5
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    reviewer = db.relationship('User', foreign_keys=[reviewer_id], backref=db.backref('reviews_given', lazy='dynamic', cascade='all, delete-orphan'))
    reviewed = db.relationship('User', foreign_keys=[reviewed_id], backref=db.backref('reviews_received', lazy='dynamic', cascade='all, delete-orphan', order_by='Review.created_at.desc()'))