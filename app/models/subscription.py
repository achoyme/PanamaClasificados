from app import db
from datetime import datetime, timedelta

class SubscriptionPlan(db.Model):
    __tablename__ = 'subscription_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # Básico, Pro, Empresa
    slug = db.Column(db.String(50), unique=True, nullable=False)
    price_monthly = db.Column(db.Numeric(10, 2), nullable=False)
    price_yearly = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Features
    max_listings = db.Column(db.Integer, default=5)
    max_images_per_listing = db.Column(db.Integer, default=5)
    featured_listings_included = db.Column(db.Integer, default=0)
    analytics_access = db.Column(db.Boolean, default=False)
    priority_support = db.Column(db.Boolean, default=False)
    custom_store = db.Column(db.Boolean, default=False)  # Tienda personalizada
    commission_discount = db.Column(db.Numeric(4, 2), default=0.00)  # % descuento en comisiones
    
    is_active = db.Column(db.Boolean, default=True)

class UserSubscription(db.Model):
    __tablename__ = 'user_subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plans.id'), nullable=False)
    
    status = db.Column(db.String(20), default='Active')  # Active, Cancelled, PastDue
    billing_cycle = db.Column(db.String(10), default='monthly')  # monthly, yearly
    
    current_period_start = db.Column(db.DateTime, default=datetime.utcnow)
    current_period_end = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)
    
    # Para integración con pasarela de pago (Stripe/PayPal)
    payment_provider = db.Column(db.String(20))  # stripe, paypal, yappy
    payment_subscription_id = db.Column(db.String(100))
    
    user = db.relationship('User', backref=db.backref('subscription', uselist=False))
    plan = db.relationship('SubscriptionPlan')
    
    def is_active(self):
        return self.status == 'Active' and self.current_period_end > datetime.utcnow()