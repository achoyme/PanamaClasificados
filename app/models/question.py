from app import db
from datetime import datetime

class Question(db.Model):
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id', ondelete='CASCADE'), nullable=False)
    # user_id es quien hace la pregunta
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    content = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    answered_at = db.Column(db.DateTime)

    # Relaciones para que el anuncio sepa cuáles son sus preguntas
    listing = db.relationship('Listing', backref=db.backref('questions', lazy='dynamic', cascade='all, delete-orphan', order_by='Question.created_at.desc()'))
    user = db.relationship('User', backref=db.backref('questions_asked', lazy='dynamic', cascade='all, delete-orphan'))
