from app import db
from datetime import datetime

class AdCampaign(db.Model):
    __tablename__ = 'ad_campaigns'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    name = db.Column(db.String(100))
    ad_type = db.Column(db.String(20))  # banner, sponsored_listing, popup
    
    # Targeting
    target_categories = db.Column(db.JSON)  # [1, 2, 3]
    target_provinces = db.Column(db.JSON)  # ["Panamá", "Chiriquí"]
    target_keywords = db.Column(db.JSON)  # ["auto", "iphone"]
    
    # Budget
    daily_budget = db.Column(db.Numeric(10, 2))
    cost_per_click = db.Column(db.Numeric(6, 2), default=0.50)  # CPC
    cost_per_impression = db.Column(db.Numeric(8, 4), default=0.001)  # CPM
    
    total_spent = db.Column(db.Numeric(10, 2), default=0)
    total_clicks = db.Column(db.Integer, default=0)
    total_impressions = db.Column(db.Integer, default=0)
    
    status = db.Column(db.String(20), default='Pending')  # Pending, Active, Paused, Completed
    
    # Creatives
    image_url = db.Column(db.String(500))
    title = db.Column(db.String(100))
    description = db.Column(db.String(200))
    link_url = db.Column(db.String(500))
    
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='ad_campaigns')

class AdImpression(db.Model):
    __tablename__ = 'ad_impressions'
    
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('ad_campaigns.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Null = visitante
    ip_address = db.Column(db.String(45))
    clicked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)