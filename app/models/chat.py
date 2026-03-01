from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.extensions import db

class Conversation(db.Model):
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True)
    listing_id = Column(Integer, ForeignKey('listings.id'), nullable=False)
    buyer_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    seller_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    status = Column(String(20), default='Active')
    last_message_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    listing = relationship('Listing')
    buyer = relationship('User', foreign_keys=[buyer_user_id])
    seller = relationship('User', foreign_keys=[seller_user_id])
    messages = relationship('Message', back_populates='conversation', cascade='all, delete-orphan')

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=False)
    sender_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    message_text = Column(String(2000), nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    conversation = relationship('Conversation', back_populates='messages')
    sender = relationship('User', foreign_keys=[sender_user_id])