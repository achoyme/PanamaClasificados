from app import db
from datetime import datetime

class ContactMessage(db.Model):
    __tablename__ = 'contact_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'), nullable=False)
    sender_name = db.Column(db.String(100), nullable=False)
    sender_email = db.Column(db.String(120), nullable=False)
    sender_phone = db.Column(db.String(20))
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # ✅ CORRECCIÓN: Usar back_populates (NO backref)
    listing = db.relationship('Listing', back_populates='contact_messages')