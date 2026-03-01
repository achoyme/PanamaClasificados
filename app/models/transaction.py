from app import db
from datetime import datetime

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Cantidad (puede ser dinero o cantidad de créditos)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Tipo: 'Recarga', 'Compra Paquete', 'Consumo Credito', 'Retiro'
    transaction_type = db.Column(db.String(50), nullable=False) 
    
    # Moneda/Unidad: 'USD', 'Credito Premium', 'Credito Profesional'
    currency = db.Column(db.String(30), default='USD')
    
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relación bidireccional
    user = db.relationship('User', backref=db.backref('transactions', lazy=True, cascade="all, delete-orphan"))