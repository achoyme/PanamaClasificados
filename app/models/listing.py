from app import db
from datetime import datetime

class Listing(db.Model):
    __tablename__ = 'listings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    
    province = db.Column(db.String(100), nullable=False)
    district = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100))
    condition = db.Column(db.String(50))
    is_negotiable = db.Column(db.Boolean, default=False)
    
    # Atributos Dinámicos (JSON)
    attributes = db.Column(db.JSON)

    tier = db.Column(db.String(50), default='Gratis')
    duration_days = db.Column(db.Integer, default=30)
    
    status = db.Column(db.String(20), default='Active')
    view_count = db.Column(db.Integer, default=0)
    
    virtual_tour_url = db.Column(db.String(500))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)

    # ==========================================
    # RELACIONES (Aquí faltaba el usuario)
    # ==========================================
    user = db.relationship('User', back_populates='listings')
    category = db.relationship('Category', backref='listings')
    images = db.relationship('Image', backref='listing', cascade='all, delete-orphan', order_by='Image.display_order')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'price': float(self.price),
            'province': self.province,
            'attributes': self.attributes,
            'created_at': self.created_at.isoformat()
        }
