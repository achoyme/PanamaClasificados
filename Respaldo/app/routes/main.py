from flask import Blueprint, render_template
from app.models import Listing

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    recent_listings = Listing.query.filter_by(status='Active').order_by(Listing.created_at.desc()).limit(8).all()
    return render_template('index.html', listings=recent_listings)
